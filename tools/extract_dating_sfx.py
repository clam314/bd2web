#!/usr/bin/env python3
"""从 Visual_Novel_SFX bank 提取指定心契角色的完整 SFX。

保留事件时间轴里直接引用的全部 sample，包括角色专属音效和公共衣料、液体、
碰撞音效。当前 BD2 bank 的目标事件全部由 WAIT / MUIT 构成，因此可以准确
还原每个触发时间、播放窗口和加权随机池；不会递归猜测未被时间轴直接引用的声音。

示例：
  PYTHONPATH=/private/tmp/bd2-python-deps python3 tools/extract_dating_sfx.py \
    --dating-id illust_dating18 \
    --char-id char000396 \
    --source-version 20260616170924 \
    --bank /private/tmp/bd2-current-audio/visual_interaction_sfx.updated \
    --fsb /private/tmp/bd2-current-audio/visual_novel_sfx.fsb \
    --event-paths /private/tmp/bd2-device-soundmaster/char000396-paths.tsv \
    --vgmstream /private/tmp/vgmstream-build-r2117/cli/vgmstream-cli \
    --alias mix6_7_2=mix6_7_1 \
    --alias mix6_7_3=mix6_7_1 \
    --alias mix6_7_4=mix6_7_1 \
    --alias mix6_7_5=mix6_7_1 \
    --alias mix6_7_6=mix6_7_1 \
    --decode
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

from extract_dating_audio import (
    ROOT,
    decode_ogg,
    load_event_paths,
    parse_fev,
    round_seconds,
    safe_filename,
    sha256,
    vgmstream_metadata,
)


def normalize_action_name(name: str) -> str:
    """统一 FMOD 的补零命名与 Spine 动画名，如 mix6_07_1 -> mix6_7_1。"""
    return re.sub(r"\d+", lambda match: str(int(match.group())), name)


def parse_aliases(values: list[str]) -> dict[str, str]:
    aliases = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"alias 必须是 animation=event：{value}")
        animation, event = value.split("=", 1)
        aliases[normalize_action_name(animation)] = normalize_action_name(event)
    return aliases


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dating-id", required=True)
    parser.add_argument("--char-id", required=True)
    parser.add_argument("--source-version", required=True)
    parser.add_argument("--bank", type=Path, required=True)
    parser.add_argument("--fsb", type=Path, required=True)
    parser.add_argument("--event-paths", type=Path, required=True)
    parser.add_argument(
        "--vgmstream",
        type=Path,
        default=Path(shutil.which("vgmstream-cli") or "vgmstream-cli"),
    )
    parser.add_argument(
        "--ffmpeg",
        type=Path,
        default=Path(shutil.which("ffmpeg") or "ffmpeg"),
    )
    parser.add_argument("--alias", action="append", default=[])
    parser.add_argument(
        "--expect-events",
        type=int,
        help="可选验收断言：期望 SFX 事件数",
    )
    parser.add_argument(
        "--expect-triggers",
        type=int,
        help="可选验收断言：期望 Timeline 触发点数",
    )
    parser.add_argument(
        "--expect-samples",
        type=int,
        help="可选验收断言：期望直接引用 sample 数",
    )
    parser.add_argument(
        "--output-data",
        type=Path,
        default=ROOT / "data" / "dating_audio.json",
    )
    parser.add_argument("--audio-dir", type=Path)
    parser.add_argument("--decode", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    bank_path = args.bank.resolve()
    fsb_path = args.fsb.resolve()
    graph = parse_fev(bank_path.read_bytes())
    metadata = vgmstream_metadata(args.vgmstream, fsb_path)
    paths = load_event_paths(args.event_paths.resolve())
    samples = {}
    events = {}
    actions = {}
    used_streams = set()

    for event_guid, timeline_guid in graph["events"].items():
        event_path = paths.get(event_guid, "")
        if f"/{args.char_id.capitalize()}/Interaction/" not in event_path:
            continue
        event_name = normalize_action_name(event_path.rsplit("/", 1)[-1])
        triggers = []
        for ref in graph["timelines"].get(timeline_guid, []):
            instrument_guid = ref["instrument"]
            choices_raw = graph["multiInstruments"].get(
                instrument_guid,
                [{"wait": instrument_guid, "weight": 100.0}],
            )
            choices = []
            for choice in choices_raw:
                wav_guid = graph["waits"].get(choice["wait"])
                stream_index = graph["waves"].get(wav_guid)
                if stream_index is None:
                    continue
                sample = metadata.get(stream_index)
                if not sample:
                    raise ValueError(f"FSB 缺少 stream index {stream_index}")
                sample_name = sample["name"]
                used_streams.add(stream_index)
                samples[sample_name] = {
                    **sample,
                    "file": f"{safe_filename(sample_name)}.ogg",
                }
                choices.append(
                    {
                        "sample": sample_name,
                        "weight": round(choice["weight"], 6),
                    }
                )
            if choices:
                triggers.append(
                    {
                        "at": round_seconds(ref["startTicks"]),
                        "window": round_seconds(ref["durationTicks"]),
                        "choices": choices,
                    }
                )
        if not triggers:
            continue
        triggers.sort(key=lambda item: item["at"])
        events[event_name] = {
            "guid": event_guid,
            "path": event_path,
            "triggers": triggers,
        }
        actions[event_name] = event_name

    aliases = parse_aliases(args.alias)
    for animation, event_name in aliases.items():
        if event_name not in events:
            raise ValueError(f"alias 指向不存在的事件：{animation}={event_name}")
        actions[animation] = event_name

    trigger_count = sum(len(event["triggers"]) for event in events.values())
    if args.expect_events is not None and len(events) != args.expect_events:
        raise ValueError(f"预期 SFX 事件 {args.expect_events} 个，实际 {len(events)}")
    if args.expect_triggers is not None and trigger_count != args.expect_triggers:
        raise ValueError(
            f"预期 SFX 触发点 {args.expect_triggers} 个，实际 {trigger_count}"
        )
    if args.expect_samples is not None and len(samples) != args.expect_samples:
        raise ValueError(
            f"预期直接引用 SFX {args.expect_samples} 个，实际 {len(samples)}"
        )

    output = args.output_data.resolve()
    document = json.loads(output.read_text(encoding="utf-8"))
    character = document["characters"].get(args.dating_id)
    if not character:
        character = {
            "charId": args.char_id,
            "sourceVersion": args.source_version,
            "language": document.get("defaultLanguage", "KR"),
            "audioBase": f"./audio/dating/{args.dating_id}/voice/",
            "bank": None,
            "samples": {},
            "events": {},
            "actions": {},
        }
        document["characters"][args.dating_id] = character
    character["sfx"] = {
        "sourceVersion": args.source_version,
        "audioBase": f"./audio/dating/{args.dating_id}/sfx/",
        "bank": {
            "guid": graph["bankGuid"],
            "bankSha256": sha256(bank_path),
            "fsbSha256": sha256(fsb_path),
            "codec": "FMOD FADPCM",
            "scope": "direct-timeline-complete",
        },
        "samples": dict(sorted(samples.items())),
        "events": dict(sorted(events.items())),
        "actions": dict(sorted(actions.items())),
    }
    output.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    audio_dir = (
        args.audio_dir.resolve()
        if args.audio_dir
        else ROOT / "audio" / "dating" / args.dating_id / "sfx"
    )
    if args.decode:
        audio_dir.mkdir(parents=True, exist_ok=True)
        ordered = sorted(samples.values(), key=lambda item: item["stream"])
        for index, sample in enumerate(ordered, 1):
            target = audio_dir / sample["file"]
            print(f"[{index:02d}/{len(ordered):02d}] {sample['name']} -> {target.name}")
            decode_ogg(
                args.vgmstream,
                args.ffmpeg,
                fsb_path,
                sample["stream"],
                target,
            )

    print(
        f"完成：{len(samples)} 个完整 SFX，{len(events)} 个事件，"
        f"{trigger_count} 个触发点，{len(actions)} 个动画映射"
    )
    print(f"数据：{output}")
    if args.decode:
        print(f"音频：{audio_dir}")


if __name__ == "__main__":
    main()
