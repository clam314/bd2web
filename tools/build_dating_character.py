#!/usr/bin/env python3
"""批量接入单个心契角色的热区与互动语音。

这个工具把 Nebris 跑通的流程串起来，避免后续角色继续手工拼命令：

1. 从 dating prefab bundle 导出 skeleton-space 热区 JSON；
2. 从 dating prefab bundle 导出互动 action JSON；
3. 从 interaction voice bundle 解出 FEV bank / FSB；
4. 调用 `extract_dating_audio.py` 生成 voice OGG 与 manifest；
5. 调用 `apply_dating_interaction_voice_actions.py` 写入 point-based `interactionVoices`；
6. 默认禁用该角色 SFX，避免 Nebris 那类混杂 SFX 误播；
7. 做基础引用/文件校验。

热区 JSON 是证据产物。传 `--update-hotzones-data` 时会合并进
`data/dating_hotzones.json`，前端会优先读取该外部文件；`dating.html`
里的旧 `PREFAB_HOTZONES` 只作为兜底。

action JSON 同理。传 `--update-actions-data` 时会合并进
`data/dating_actions.json`，前端会优先读取它；旧手写
`PREFAB_POINT_ACTIONS` 只作为兜底。
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def run(cmd: list[str], *, env=None):
    print("+", " ".join(str(item) for item in cmd))
    subprocess.run(cmd, cwd=ROOT, check=True, env=env)


def extract_bank(bundle: Path) -> bytes:
    from extract_dating_audio import extract_bank as _extract_bank

    return _extract_bank(bundle)


def extract_fsb(bank_blob: bytes) -> bytes:
    offset = bank_blob.find(b"FSB5")
    if offset < 0:
        raise ValueError("FEV bank 中找不到 FSB5 magic")
    return bank_blob[offset:]


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def verify_manifest(dating_id: str, audio_dir: Path, manifest: Path, *, check_files: bool = True):
    doc = json.loads(manifest.read_text(encoding="utf-8"))
    character = doc["characters"][dating_id]
    bad_voice_refs = []
    for key, item in character.get("interactionVoices", {}).items():
        for phase, refs in item.items():
            if isinstance(refs, str):
                refs = [refs]
            for ref in refs:
                if ref not in character.get("events", {}):
                    bad_voice_refs.append((key, phase, ref))

    missing_files = []
    if check_files:
        for sample in character.get("samples", {}).values():
            rel = sample.get("file") or sample.get("src")
            if not rel:
                missing_files.append(f"{sample.get('name', '?')}: missing file field")
                continue
            path = Path(rel)
            if not path.is_absolute():
                path = audio_dir / rel
            if not path.exists():
                missing_files.append(str(path))

    print(
        f"verify {dating_id}: events={len(character.get('events', {}))}, "
        f"samples={len(character.get('samples', {}))}, "
        f"interactionVoices={len(character.get('interactionVoices', {}))}, "
        f"badVoiceRefs={len(bad_voice_refs)}, missingFiles={len(missing_files)}"
    )
    if bad_voice_refs:
        raise SystemExit(f"voice 引用不存在：{bad_voice_refs[:10]}")
    if missing_files:
        raise SystemExit(f"音频文件缺失：{missing_files[:10]}")


def merge_hotzones_data(dating_id: str, hotzones: dict, output: Path):
    if output.exists():
        doc = json.loads(output.read_text(encoding="utf-8"))
    else:
        doc = {}
    doc[dating_id] = hotzones.get(dating_id, {})
    write_json(output, {key: doc[key] for key in sorted(doc)})
    print(f"{output}: updated {dating_id} hotzones={len(doc[dating_id])}")


def merge_actions_data(dating_id: str, actions: dict, output: Path):
    if output.exists():
        doc = json.loads(output.read_text(encoding="utf-8"))
    else:
        doc = {}
    doc[dating_id] = actions.get(dating_id, {})
    write_json(output, {key: doc[key] for key in sorted(doc)})
    print(f"{output}: updated {dating_id} actions={len(doc[dating_id])}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dating-id", required=True, help="例如 illust_dating1")
    parser.add_argument("--char-id", required=True, help="例如 char003303")
    parser.add_argument("--gid", type=int, required=True, help="SpineInteractionPointTable gid")
    parser.add_argument("--source-version", required=True)
    parser.add_argument("--voice-bundle", type=Path, required=True, help="interaction_charXXXXXX Unity bundle")
    parser.add_argument(
        "--prefab-bundle",
        type=Path,
        default=ROOT / "local_device_cache" / "bd2_current_20260624" / "common-char-datingillust_assets_all.bundle",
    )
    parser.add_argument(
        "--raw-log",
        type=Path,
        default=ROOT / "tools" / "il2cpp-re" / "all_interaction_tables_raw.log",
    )
    parser.add_argument(
        "--event-paths",
        type=Path,
        help="GUID<TAB>event path；缺省时创建空文件并使用 --infer-event-paths-from-samples",
    )
    parser.add_argument("--language", default="KR")
    parser.add_argument("--expect-events", type=int)
    parser.add_argument("--expect-samples", type=int)
    parser.add_argument("--no-decode", action="store_true", help="只更新 manifest，不转 OGG")
    parser.add_argument("--keep-sfx", action="store_true", help="不写入 sfx.disabled=true；默认禁用 SFX")
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=ROOT / "local_device_cache" / "dating_build",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "data" / "dating_audio.json",
    )
    parser.add_argument(
        "--hotzones-out",
        type=Path,
        default=ROOT / "local_device_cache" / "dating_build" / "dating_hotzones.json",
    )
    parser.add_argument(
        "--hotzones-data",
        type=Path,
        default=ROOT / "data" / "dating_hotzones.json",
    )
    parser.add_argument(
        "--update-hotzones-data",
        action="store_true",
        help="把本角色热区合并进 data/dating_hotzones.json，供前端自动读取",
    )
    parser.add_argument(
        "--actions-out",
        type=Path,
        default=ROOT / "local_device_cache" / "dating_build" / "dating_actions.json",
    )
    parser.add_argument(
        "--actions-data",
        type=Path,
        default=ROOT / "data" / "dating_actions.json",
    )
    parser.add_argument(
        "--update-actions-data",
        action="store_true",
        help="把本角色互动 action 合并进 data/dating_actions.json，供前端自动读取",
    )
    args = parser.parse_args()

    python = sys.executable
    args.work_dir.mkdir(parents=True, exist_ok=True)
    char_work = args.work_dir / args.char_id.lower()
    char_work.mkdir(parents=True, exist_ok=True)

    hotzones_path = args.hotzones_out.resolve()
    hotzones_json = subprocess.check_output(
        [
            python,
            "tools/extract_dating_hotzones.py",
            "--bundle",
            str(args.prefab_bundle.resolve()),
            "--dating-id",
            args.dating_id,
        ],
        cwd=ROOT,
    )
    hotzones_path.parent.mkdir(parents=True, exist_ok=True)
    hotzones_path.write_bytes(hotzones_json)
    hotzones = json.loads(hotzones_json)
    print(f"hotzones {args.dating_id}: {len(hotzones.get(args.dating_id, {}))}")
    if args.update_hotzones_data:
        merge_hotzones_data(args.dating_id, hotzones, args.hotzones_data.resolve())

    actions_path = args.actions_out.resolve()
    actions_json = subprocess.check_output(
        [
            python,
            "tools/extract_dating_actions.py",
            "--bundle",
            str(args.prefab_bundle.resolve()),
            "--dating-id",
            args.dating_id,
        ],
        cwd=ROOT,
    )
    actions_path.parent.mkdir(parents=True, exist_ok=True)
    actions_path.write_bytes(actions_json)
    actions = json.loads(actions_json)
    print(f"actions {args.dating_id}: {len(actions.get(args.dating_id, {}))}")
    if args.update_actions_data:
        merge_actions_data(args.dating_id, actions, args.actions_data.resolve())

    bank_path = char_work / f"interaction_{args.char_id.lower()}.bank"
    fsb_path = char_work / f"interaction_{args.char_id.lower()}.fsb"
    bank_blob = extract_bank(args.voice_bundle.resolve())
    bank_path.write_bytes(bank_blob)
    fsb_path.write_bytes(extract_fsb(bank_blob))
    print(f"bank: {bank_path}")
    print(f"fsb : {fsb_path}")

    event_paths = args.event_paths
    if event_paths is None:
        event_paths = char_work / f"{args.char_id.capitalize()}.tsv"
        event_paths.write_text("", encoding="utf-8")

    audio_cmd = [
        python,
        "tools/extract_dating_audio.py",
        "--dating-id",
        args.dating_id,
        "--char-id",
        args.char_id,
        "--source-version",
        args.source_version,
        "--bundle",
        str(args.voice_bundle.resolve()),
        "--fsb",
        str(fsb_path),
        "--event-paths",
        str(event_paths.resolve()),
        "--infer-event-paths-from-samples",
        "--language",
        args.language,
        "--output-data",
        str(args.manifest.resolve()),
    ]
    if not args.no_decode:
        audio_cmd.append("--decode")
    if args.expect_events is not None:
        audio_cmd += ["--expect-events", str(args.expect_events)]
    if args.expect_samples is not None:
        audio_cmd += ["--expect-samples", str(args.expect_samples)]
    run(audio_cmd)

    run(
        [
            python,
            "tools/apply_dating_interaction_voice_actions.py",
            "--dating-id",
            args.dating_id,
            "--char-id",
            args.char_id,
            "--gid",
            str(args.gid),
            "--raw-log",
            str(args.raw_log.resolve()),
            "--manifest",
            str(args.manifest.resolve()),
            "--hotzones-json",
            str(hotzones_path),
        ]
    )

    if not args.keep_sfx:
        doc = json.loads(args.manifest.read_text(encoding="utf-8"))
        character = doc["characters"][args.dating_id]
        character.setdefault("sfx", {})["disabled"] = True
        write_json(args.manifest, doc)
        print(f"{args.dating_id}: sfx.disabled=true")

    verify_manifest(
        args.dating_id,
        ROOT / "audio" / "dating" / args.dating_id / "voice",
        args.manifest.resolve(),
        check_files=not args.no_decode,
    )

    if args.update_hotzones_data:
        print("完成。热区已合并到 data/dating_hotzones.json，前端会自动读取。")
    else:
        print("完成。热区 JSON 已生成；确认后可用 --update-hotzones-data 合并给前端读取。")


if __name__ == "__main__":
    if shutil.which("vgmstream-cli") is None:
        print("warning: vgmstream-cli not found in PATH; --no-decode may still work", file=sys.stderr)
    main()
