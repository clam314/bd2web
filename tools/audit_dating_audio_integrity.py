#!/usr/bin/env python3
"""Audit dating audio wiring without mutating the playable manifest.

The important invariant is:

    illust_datingN -> charId comes only from data/dating_charid_map.json

Every FMOD path and every existing data/dating_audio.json entry is checked
against that charId before it can be considered safe.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from extract_dating_audio import load_event_paths, parse_fev
from extract_dating_sfx import normalize_action_name


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVENT_PATHS = (
    ROOT / "local_device_cache" / "bd2_current_20260624" / "all-fmod-event-paths.tsv"
)
DEFAULT_VISUAL_BANK = (
    ROOT
    / "local_device_cache"
    / "bd2_current_20260624"
    / "visual_interaction_sfx"
    / "visual_interaction_sfx.bank"
)


CHAR_RE = re.compile(r"Char\d{6}", re.IGNORECASE)


def sort_dating_key(value: str) -> int:
    match = re.search(r"(\d+)$", value)
    return int(match.group(1)) if match else 9999


def canonical_char_id(value: str) -> str:
    value = value.strip()
    match = CHAR_RE.search(value)
    if not match:
        return value.lower()
    return match.group(0).lower()


def extract_char_id(path: str) -> str | None:
    match = CHAR_RE.search(path or "")
    return canonical_char_id(match.group(0)) if match else None


# 已实证的跨 charId 命名别名(游戏数据本身如此,不是串号):
# char004202(帕莱特/dating17)自己的 interaction bank 里,mix 动作语音事件全部
# 命名为 Char004102_Int_*(疑似从提尔项目复制),samples 在 char004202 自己的
# fsb 内(bank/fsb sha256 与 manifest 记录一致)。2026-07-03 逐事件验证。
KNOWN_PATH_ALIASES: dict[str, set[str]] = {
    "char004202": {"char004102"},
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def required_actions(action_entry) -> list[str]:
    needed: set[str] = set()
    if not isinstance(action_entry, dict):
        return []
    for value in action_entry.values():
        if isinstance(value, dict):
            for name in value.get("mix", []) or []:
                if isinstance(name, str) and name:
                    needed.add(normalize_action_name(name))
    return sorted(needed)


def voice_path_kind(path: str) -> str:
    lowered = path.lower()
    if "/voices/common/" in lowered and "/interaction/" in lowered:
        if "_int_mix" in lowered:
            return "voiceMix"
        return "voiceInt"
    if "/cinematic/visual_novel/" in lowered and "/interaction/" in lowered:
        return "sfx"
    return "other"


def index_event_paths(path: Path) -> dict[str, dict[str, list[dict[str, str]]]]:
    by_char: dict[str, dict[str, list[dict[str, str]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    if not path.exists():
        return by_char
    for guid, event_path in load_event_paths(path).items():
        char_id = extract_char_id(event_path)
        if not char_id:
            continue
        kind = voice_path_kind(event_path)
        if kind == "other":
            continue
        by_char[char_id][kind].append({"guid": guid, "path": event_path})
    return by_char


def has_playable_timeline(graph: dict, timeline_guid: str) -> bool:
    for ref in graph["timelines"].get(timeline_guid, []):
        instrument_guid = ref["instrument"]
        choices = graph["multiInstruments"].get(
            instrument_guid,
            [{"wait": instrument_guid, "weight": 100.0}],
        )
        for choice in choices:
            wav_guid = graph["waits"].get(choice["wait"])
            if graph["waves"].get(wav_guid) is not None:
                return True
    return False


def visual_bank_events(bank_path: Path, all_paths: Path) -> dict[str, set[str]]:
    if not bank_path.exists() or not all_paths.exists():
        return {}
    graph = parse_fev(bank_path.read_bytes())
    paths = load_event_paths(all_paths)
    by_char: dict[str, set[str]] = defaultdict(set)
    for event_guid, timeline_guid in graph["events"].items():
        event_path = paths.get(event_guid, "")
        if voice_path_kind(event_path) != "sfx":
            continue
        if not has_playable_timeline(graph, timeline_guid):
            continue
        char_id = extract_char_id(event_path)
        if not char_id:
            continue
        action = normalize_action_name(event_path.rsplit("/", 1)[-1])
        by_char[char_id].add(action)
    return by_char


def manifest_path_issues(dating_id: str, char_id: str, character: dict) -> list[str]:
    issues: list[str] = []
    if canonical_char_id(character.get("charId", "")) != char_id:
        issues.append(
            f"manifest charId={character.get('charId')} != map charId={char_id}"
        )
    checks = [
        ("voiceEvents", character.get("events", {})),
        ("voiceActionEvents", character.get("actions", {})),
        ("sfxEvents", character.get("sfx", {}).get("events", {})),
    ]
    for label, items in checks:
        if not isinstance(items, dict):
            continue
        for name, value in items.items():
            if label == "voiceActionEvents" and isinstance(value, str):
                # action aliases point to another event name, not a path.
                continue
            if not isinstance(value, dict):
                continue
            path = value.get("path", "")
            path_char = extract_char_id(path)
            if (
                path
                and path_char != char_id
                and path_char not in KNOWN_PATH_ALIASES.get(char_id, set())
            ):
                issues.append(f"{label}.{name} path char={path_char} != {char_id}")
    sfx_actions = character.get("sfx", {}).get("actions", {})
    sfx_events = character.get("sfx", {}).get("events", {})
    if isinstance(sfx_actions, dict) and isinstance(sfx_events, dict):
        for animation, event_name in sfx_actions.items():
            if event_name not in sfx_events:
                issues.append(f"sfx action {animation} -> missing event {event_name}")
    return issues


def write_markdown(report: dict, path: Path) -> None:
    lines: list[str] = []
    lines.append("# Dating Audio Integrity Audit")
    lines.append("")
    lines.append(f"- Generated: {report['generated']}")
    lines.append(
        "- Rule: `illust_datingN -> charId` is read only from "
        "`data/dating_charid_map.json`; gid/menu numbers are not used as keys."
    )
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Characters in map: {report['summary']['charactersInMap']}")
    lines.append(f"- Manifest path issues: {report['summary']['manifestPathIssues']}")
    lines.append(f"- PointTable characters: {report['summary']['pointTableCharacters']}")
    lines.append(f"- PointTable gid != dating number: {report['summary']['gidNotDatingNumber']}")
    lines.append(f"- Safe visual SFX candidates: {report['summary']['safeVisualSfxCandidates']}")
    lines.append(f"- Needs alias/review: {report['summary']['needsAliasOrReview']}")
    lines.append(f"- Needs other bank: {report['summary']['needsOtherBank']}")
    lines.append(f"- Missing action table: {report['summary']['missingActionTable']}")
    lines.append("")
    lines.append("## Per character")
    lines.append("")
    lines.append(
        "| dating | charId | PointTable gid | source | actions | manifest missing | visual bank | matched | raw missing | status |"
    )
    lines.append("|---|---|---:|---|---:|---:|---:|---:|---:|---|")
    for row in report["characters"]:
        gid = row["interactionTable"]["gid"]
        gid_text = str(gid) if gid is not None else "-"
        lines.append(
            "| {datingId} | {charId} | {gid} | {name} / {costume} | {requiredActionCount} | "
            "{manifest_missing} | "
            "{visualBankEventCount} | {visualBankMatchedCount} | {visualBankMissingCount} | "
            "{recommendedStatus} |".format(
                **row,
                gid=gid_text,
                manifest_missing=row["manifest"]["requiredActionMissingCount"],
            )
        )
    lines.append("")
    lines.append("## Detail flags")
    lines.append("")
    for row in report["characters"]:
        flags = []
        if row["manifestIssues"]:
            flags.append("manifest issues: " + "; ".join(row["manifestIssues"]))
        if row["manifest"]["requiredActionMissing"]:
            flags.append(
                "manifest required-action missing: "
                + ", ".join(row["manifest"]["requiredActionMissing"][:24])
            )
        if row["visualBankMissing"]:
            flags.append("visual missing: " + ", ".join(row["visualBankMissing"][:24]))
        if row["visualBankExtra"]:
            flags.append("visual extra: " + ", ".join(row["visualBankExtra"][:24]))
        if flags:
            lines.append(f"### {row['datingId']} / {row['charId']}")
            lines.append("")
            for flag in flags:
                lines.append(f"- {flag}")
            lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-paths", type=Path, default=DEFAULT_EVENT_PATHS)
    parser.add_argument("--visual-bank", type=Path, default=DEFAULT_VISUAL_BANK)
    parser.add_argument(
        "--out-json",
        type=Path,
        default=ROOT / "local_device_cache" / "dating_audio_integrity_audit.json",
    )
    parser.add_argument(
        "--out-md",
        type=Path,
        default=ROOT / "local_device_cache" / "dating_audio_integrity_audit.md",
    )
    args = parser.parse_args()

    char_map = load_json(ROOT / "data" / "dating_charid_map.json")["map"]
    actions = load_json(ROOT / "data" / "dating_actions.json")
    audio = load_json(ROOT / "data" / "dating_audio.json")["characters"]
    point_tables = load_json(ROOT / "data" / "dating_interaction_tables.json").get(
        "characters", {}
    )
    interaction_meta = load_json(ROOT / "data" / "dating_interaction_meta.json").get(
        "characters", {}
    )
    events_by_char = index_event_paths(args.event_paths)
    visual_events_by_char = visual_bank_events(args.visual_bank, args.event_paths)

    rows = []
    for dating_id, info in sorted(char_map.items(), key=lambda item: sort_dating_key(item[0])):
        char_id = canonical_char_id(info["charId"])
        needed = set(required_actions(actions.get(dating_id)))
        visual_events = visual_events_by_char.get(char_id, set())
        matched = needed & visual_events
        missing = needed - visual_events
        extra = visual_events - needed
        all_fmod_counts = {
            kind: len(events_by_char.get(char_id, {}).get(kind, []))
            for kind in ("voiceInt", "voiceMix", "sfx")
        }
        manifest = audio.get(dating_id, {})
        manifest_issues = manifest_path_issues(dating_id, char_id, manifest)
        manifest_sfx_actions = set(
            manifest.get("sfx", {}).get("actions", {}).keys()
            if isinstance(manifest.get("sfx", {}).get("actions", {}), dict)
            else []
        )
        manifest_action_missing = sorted(needed - manifest_sfx_actions)
        point_table = point_tables.get(char_id, {})
        meta = interaction_meta.get(char_id, {})
        gid = point_table.get("gid", meta.get("gid"))
        bank_name = meta.get("SoundVoiceBankName")
        if bank_name:
            bank_char = extract_char_id(bank_name)
            if bank_char and bank_char != char_id:
                manifest_issues.append(
                    f"interaction meta bank {bank_name} char={bank_char} != {char_id}"
                )

        if not needed:
            status = "missing-action-table"
        elif visual_events and not missing:
            status = "safe-visual-sfx"
        elif visual_events and missing:
            status = "needs-alias-or-review"
        elif all_fmod_counts["sfx"]:
            status = "needs-other-bank"
        else:
            status = "no-sfx-evidence"

        rows.append(
            {
                "datingId": dating_id,
                "charId": char_id,
                "name": info.get("name", ""),
                "costume": info.get("costume", ""),
                "requiredActions": sorted(needed),
                "requiredActionCount": len(needed),
                "visualBankEvents": sorted(visual_events),
                "visualBankEventCount": len(visual_events),
                "visualBankMatched": sorted(matched),
                "visualBankMatchedCount": len(matched),
                "visualBankMissing": sorted(missing),
                "visualBankMissingCount": len(missing),
                "visualBankExtra": sorted(extra),
                "visualBankExtraCount": len(extra),
                "allFmodCounts": all_fmod_counts,
                "interactionTable": {
                    "hasPointTable": bool(point_table),
                    "gid": gid,
                    "interactionGroupId": point_table.get("interactionGroupId"),
                    "gidEqualsDatingNumber": gid == sort_dating_key(dating_id),
                    "soundVoiceBankName": bank_name,
                },
                "manifest": {
                    "hasCharacter": dating_id in audio,
                    "voiceEventCount": len(manifest.get("events", {})),
                    "voiceActionCount": len(manifest.get("actions", {})),
                    "sfxActionCount": len(manifest.get("sfx", {}).get("actions", {})),
                    "sfxEventCount": len(manifest.get("sfx", {}).get("events", {})),
                    "requiredActionMissing": manifest_action_missing,
                    "requiredActionMissingCount": len(manifest_action_missing),
                },
                "manifestIssues": manifest_issues,
                "recommendedStatus": status,
            }
        )

    status_counts = Counter(row["recommendedStatus"] for row in rows)
    report = {
        "generated": "2026-07-01",
        "inputs": {
            "charMap": "data/dating_charid_map.json",
            "actions": "data/dating_actions.json",
            "audio": "data/dating_audio.json",
            "eventPaths": str(args.event_paths.relative_to(ROOT)),
            "visualBank": str(args.visual_bank.relative_to(ROOT)),
        },
        "summary": {
            "charactersInMap": len(rows),
            "manifestPathIssues": sum(1 for row in rows if row["manifestIssues"]),
            "pointTableCharacters": sum(
                1 for row in rows if row["interactionTable"]["hasPointTable"]
            ),
            "gidNotDatingNumber": sum(
                1
                for row in rows
                if row["interactionTable"]["hasPointTable"]
                and not row["interactionTable"]["gidEqualsDatingNumber"]
            ),
            "safeVisualSfxCandidates": status_counts["safe-visual-sfx"],
            "needsAliasOrReview": status_counts["needs-alias-or-review"],
            "needsOtherBank": status_counts["needs-other-bank"],
            "missingActionTable": status_counts["missing-action-table"],
            "statusCounts": dict(sorted(status_counts.items())),
        },
        "characters": rows,
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_markdown(report, args.out_md)
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))
    print(args.out_json)
    print(args.out_md)


if __name__ == "__main__":
    main()
