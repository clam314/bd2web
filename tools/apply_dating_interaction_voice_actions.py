#!/usr/bin/env python3
"""把 SpineInteractionPointTable 抓取结果合并到 dating_audio.json。

游戏表里是 ``(interactionGroupId, groupId, id) -> SoundVoiceName``，本工具会生成
``character.interactionVoices``，让前端按真实互动点 key 播 voice：

  - 普通点击/拖拽：``<groupId>_<id>_0.voice``
  - 阶段推进 motion：``<groupId>_<id>_0.motion``

同时为了兼容旧版前端，也可继续生成按动画名索引的 ``actions``。raw log 中 repeated 字段的
重复项会被原样保留，让前端可以按重复次数做简单权重随机。
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def short_voice_name(path: str, char_id: str) -> str | None:
    prefix = f"{char_id.capitalize()}_Int_"
    name = path.rsplit("/", 1)[-1]
    if not name.startswith(prefix):
        return None
    return name[len(prefix) :]


def parse_raw_log(path: Path, gid: int, char_id: str):
    rx = re.compile(
        r"^gid=(\d+) ig=(\d+) g=(-?\d+) id=(\d+) "
        r"VOICE=\[(.*?)\] MOTION=\[(.*?)\]$"
    )
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = rx.match(line)
        if not match:
            continue
        row_gid, _ig, group_id, point_id, voice_raw, motion_raw = match.groups()
        if int(row_gid) != gid:
            continue
        voice = [
            short
            for item in voice_raw.split("|")
            if item
            for short in [short_voice_name(item, char_id)]
            if short
        ]
        motion = [
            short
            for item in motion_raw.split("|")
            if item
            for short in [short_voice_name(item, char_id)]
            if short
        ]
        rows[(int(group_id), int(point_id))] = {"voice": voice, "motion": motion}
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dating-id", required=True, help="例如 illust_dating1")
    parser.add_argument("--char-id", required=True, help="例如 char003303")
    parser.add_argument("--gid", type=int, required=True)
    parser.add_argument(
        "--legacy-animation-actions",
        action="store_true",
        help="同时生成旧版 actions[mix*/motion*] 映射；默认只生成 point-based interactionVoices",
    )
    parser.add_argument(
        "--raw-log",
        type=Path,
        default=ROOT / "tools" / "il2cpp-re" / "all_interaction_tables_raw.log",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "data" / "dating_audio.json",
    )
    parser.add_argument(
        "--hotzones-json",
        type=Path,
        help="可选：extract_dating_hotzones.py 输出。用于把同一 group/id 映射到所有 toolId 变体。",
    )
    args = parser.parse_args()

    doc = json.loads(args.manifest.read_text(encoding="utf-8"))
    character = doc["characters"][args.dating_id]
    events = set(character.get("events", {}))
    sfx_actions = set(character.get("sfx", {}).get("actions", {}))
    rows = parse_raw_log(args.raw_log, args.gid, args.char_id)
    hotzone_keys = []
    if args.hotzones_json and args.hotzones_json.exists():
        hotzones = json.loads(args.hotzones_json.read_text(encoding="utf-8"))
        hotzone_keys = sorted((hotzones.get(args.dating_id) or {}).keys())

    actions = {}
    interaction_voices = {}
    missing_events = set()

    for (group_id, point_id), row in sorted(rows.items()):
        voice = [name for name in row["voice"] if name in events]
        motion = [name for name in row["motion"] if name in events]
        missing_events.update(name for name in row["voice"] + row["motion"] if name not in events)

        if voice or motion:
            # The game table has no tool id.  When hotzone/prefab keys are
            # available, map the row to every stage_point_tool variant; otherwise
            # fall back to tool 0 for simple characters like Nebris.
            prefix = f"{group_id}_{point_id}_"
            target_keys = [key for key in hotzone_keys if key.startswith(prefix)] or [f"{group_id}_{point_id}_0"]
            for key in target_keys:
                item = {}
                if voice:
                    item["voice"] = voice
                if motion:
                    item["motion"] = motion
                interaction_voices[key] = item

        if not args.legacy_animation_actions:
            continue

        if voice:
            prefix = f"mix{group_id}_{point_id}_"
            for animation in sorted(name for name in sfx_actions if name.startswith(prefix)):
                actions[animation] = voice

        if motion:
            animation = f"motion{group_id}_{point_id}"
            if animation in sfx_actions:
                actions[animation] = motion

    character["interactionVoices"] = dict(sorted(interaction_voices.items()))
    if args.legacy_animation_actions:
        character["actions"] = dict(sorted(actions.items()))
    else:
        character["actions"] = {}
    args.manifest.write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"{args.dating_id}: {len(rows)} table rows -> "
        f"{len(interaction_voices)} interaction voice points, {len(actions)} legacy actions"
    )
    if missing_events:
        print("missing events:", ", ".join(sorted(missing_events)))


if __name__ == "__main__":
    main()
