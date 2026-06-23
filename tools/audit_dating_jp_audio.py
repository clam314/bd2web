#!/usr/bin/env python3
"""审计当前日语 SoundData 是否包含指定角色的心契语音。

用途：
  游戏更新后，把手机的 LocalVoice_JP / LocalVisualNovel_JP 拉到本地，
  再运行本工具。它会同时检查：

  1. 目标 JP event GUID 是否出现在任一 bank。
  2. FSB stream name 中是否出现角色 sample。
  3. 是否出现 Int_/Interaction 等心契特征 sample。
  4. 当前 Addressables catalog 是否发布 local_charXXXXXX_jp。

示例：
  python3 tools/audit_dating_jp_audio.py \
    --char-id char000396 \
    --event-paths /private/tmp/bd2-device-soundmaster/char000396-paths.tsv \
    --catalog /private/tmp/bd2-device-soundmaster/current-file.json \
    --bank-dir /private/tmp/bd2-localvoice-jp/LocalVoice_JP \
    --bank-dir /private/tmp/bd2-localvisual-jp \
    --vgmstream /private/tmp/vgmstream-build-r2117/cli/vgmstream-cli
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


INTERACTION_SAMPLE_RE = re.compile(
    r"(?:^|_)(?:Int|Interaction)(?:_|$)|"
    r"(?:^|_)(?:Shy[1-4]|Surprise[1-5]|Embarrass[12]|Endure[12])_",
    re.IGNORECASE,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--char-id", required=True)
    parser.add_argument("--event-paths", type=Path, required=True)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--bank-dir", type=Path, action="append", default=[])
    parser.add_argument(
        "--vgmstream",
        type=Path,
        default=Path(shutil.which("vgmstream-cli") or "vgmstream-cli"),
    )
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def jp_event_guids(path: Path, char_id: str) -> dict[str, str]:
    needle = f"/{char_id.capitalize()}/Interaction/"
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "\t" not in line:
            continue
        event_guid, event_path = line.split("\t", 1)
        if needle in event_path and event_path.endswith("_JP"):
            result[event_guid.lower()] = event_path
    return result


def bank_files(directories: list[Path]) -> list[Path]:
    files = []
    for directory in directories:
        if not directory.is_dir():
            continue
        files.extend(path for path in directory.rglob("*") if path.is_file())
    return sorted(set(files))


def stream_names(executable: Path, bank: Path, link: Path) -> list[str]:
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(bank.resolve())
    completed = subprocess.run(
        [str(executable), "-s", "1", "-S", "0", "-I", str(link)],
        capture_output=True,
        text=True,
    )
    names = []
    for line in completed.stdout.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        name = item.get("streamInfo", {}).get("name")
        if name:
            names.append(name)
    return names


def catalog_evidence(path: Path | None, char_id: str) -> dict | None:
    if not path:
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = [
        bundle.get("readableName", "")
        for bundle in document.get("bundles", [])
        if "localvisualnovel_jp" in bundle.get("readableName", "").lower()
    ]
    char_key = char_id.lower()
    return {
        "entries": len(rows),
        "characterMatches": [row for row in rows if char_key in row.lower()],
    }


def main():
    args = parse_args()
    targets = jp_event_guids(args.event_paths.resolve(), args.char_id)
    if not targets:
        raise SystemExit(f"未找到 {args.char_id} 的 JP interaction event path")

    banks = bank_files([path.resolve() for path in args.bank_dir])
    if not banks:
        raise SystemExit("没有可扫描的 bank；请至少提供一个 --bank-dir")

    guid_hits = []
    sample_hits = []
    interaction_hits = []
    char_token = args.char_id.capitalize()

    with tempfile.TemporaryDirectory(prefix="bd2-jp-audit-") as temp:
        link = Path(temp) / "scan.bank"
        for index, bank in enumerate(banks, 1):
            blob = bank.read_bytes()
            matched_guids = [
                {"guid": event_guid, "path": event_path}
                for event_guid, event_path in targets.items()
                if blob.find(bytes.fromhex(event_guid)) >= 0
            ]
            if matched_guids:
                guid_hits.append(
                    {"bank": bank.name, "size": len(blob), "events": matched_guids}
                )

            names = stream_names(args.vgmstream, bank, link)
            character_names = [name for name in names if char_token in name]
            if character_names:
                sample_hits.append(
                    {
                        "bank": bank.name,
                        "streamCount": len(names),
                        "samples": character_names,
                    }
                )
            special = [
                name
                for name in names
                if char_token in name and INTERACTION_SAMPLE_RE.search(name)
            ]
            if special:
                interaction_hits.append({"bank": bank.name, "samples": special})
            print(f"[{index:03d}/{len(banks):03d}] {bank.name}: {len(names)} streams")

    result = {
        "charId": args.char_id,
        "language": "JP",
        "targetEventCount": len(targets),
        "banksScanned": len(banks),
        "eventGuidHits": guid_hits,
        "characterSampleBanks": sample_hits,
        "interactionSampleBanks": interaction_hits,
        "catalog": catalog_evidence(args.catalog.resolve() if args.catalog else None, args.char_id),
        "available": bool(guid_hits or interaction_hits),
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"报告：{args.output}")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
