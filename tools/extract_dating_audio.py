#!/usr/bin/env python3
"""提取心契角色的 FMOD 语音事件、时间表和网页 OGG。

输入：
  1. interaction_charXXXXXX Unity bundle（或已经解出的 RIFF FEV bank）
  2. bank 内嵌的 FSB5
  3. 从当前 Master.strings 导出的 ``GUID<TAB>event path`` 文件

输出：
  - data/dating_audio.json：事件时间表、随机池权重、sample 元数据
  - audio/dating/<datingId>/voice/*.ogg：网页语音（随站点发布）

示例：
  PYTHONPATH=/private/tmp/bd2-python-deps python3 tools/extract_dating_audio.py \
    --dating-id illust_dating18 \
    --char-id char000396 \
    --source-version 20260616170924 \
    --bundle /private/tmp/bd2-current-audio/interaction_char000396.bundle \
    --fsb /private/tmp/bd2-current-audio/interaction_char000396.fsb \
    --event-paths /private/tmp/bd2-device-soundmaster/char000396-paths.tsv \
    --vgmstream /private/tmp/vgmstream-build-r2117/cli/vgmstream-cli \
    --language KR \
    --decode

项目当前统一使用 KR。JP 审计仍由 ``audit_dating_jp_audio.py`` 保留，
如果未来游戏正式发布完整心契日配，再单独评估是否切换。

RIFF FEV 结构（FMOD 2.03.x）：
  EVNT -> TMLN -> MUIT/WAIT -> WAV

TMLN 不只是“随机选一句”。长动作可在多个时间点各触发一个随机池；
本工具保留每个触发点的 start/duration，前端必须按 schedule 播放。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
UNITY_VERSION = "2021.3.40f1"
TIMELINE_TICKS_PER_SECOND = 48_000


@dataclass(frozen=True)
class Chunk:
    tag: bytes
    list_type: bytes | None
    payload_start: int
    payload_end: int


def u16(data: bytes, offset: int) -> int:
    return struct.unpack_from("<H", data, offset)[0]


def u32(data: bytes, offset: int) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def f32(data: bytes, offset: int) -> float:
    return struct.unpack_from("<f", data, offset)[0]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def guid(data: bytes) -> str:
    if len(data) != 16:
        raise ValueError(f"GUID 长度应为 16，实际为 {len(data)}")
    return data.hex()


def iter_chunks(blob: bytes, start: int, end: int):
    """遍历一个 RIFF/LIST 容器的直接子 chunk。"""
    pos = start
    while pos + 8 <= end:
        tag = blob[pos : pos + 4]
        size = u32(blob, pos + 4)
        data_start = pos + 8
        data_end = data_start + size
        if data_end > end:
            raise ValueError(
                f"RIFF chunk 越界：{tag!r} @ 0x{pos:x}, "
                f"end=0x{data_end:x}, container=0x{end:x}"
            )
        list_type = None
        payload_start = data_start
        if tag in (b"RIFF", b"LIST"):
            if size < 4:
                raise ValueError(f"无效容器 chunk：{tag!r} @ 0x{pos:x}")
            list_type = blob[data_start : data_start + 4]
            payload_start += 4
        yield Chunk(tag, list_type, payload_start, data_end)
        pos = data_end + (size & 1)


def collect_lists(blob: bytes) -> dict[bytes, list[Chunk]]:
    if blob[:4] != b"RIFF" or blob[8:12] != b"FEV ":
        raise ValueError("输入不是 RIFF FEV bank")

    result: dict[bytes, list[Chunk]] = {}

    def walk(start: int, end: int):
        for chunk in iter_chunks(blob, start, end):
            if chunk.list_type is not None:
                result.setdefault(chunk.list_type, []).append(chunk)
                walk(chunk.payload_start, chunk.payload_end)

    root_size = u32(blob, 4)
    walk(12, min(len(blob), 8 + root_size))
    return result


def direct_payload(blob: bytes, container: Chunk, wanted: bytes) -> bytes:
    for child in iter_chunks(blob, container.payload_start, container.payload_end):
        if child.tag == wanted:
            return blob[child.payload_start : child.payload_end]
    raise ValueError(
        f"{container.list_type!r} 容器缺少 {wanted!r} 子 chunk"
    )


def extract_bank(bundle: Path) -> bytes:
    try:
        import UnityPy
    except ImportError as exc:
        raise SystemExit(
            "缺少 UnityPy。请在虚拟环境安装，或临时执行：\n"
            "python3 -m pip install --target /private/tmp/bd2-python-deps UnityPy\n"
            "再用 PYTHONPATH=/private/tmp/bd2-python-deps 运行本工具。"
        ) from exc

    UnityPy.config.FALLBACK_UNITY_VERSION = UNITY_VERSION
    env = UnityPy.load(str(bundle))
    candidates: list[tuple[str, bytes]] = []
    for obj in env.objects:
        if obj.type.name != "TextAsset":
            continue
        asset = obj.read()
        script = asset.m_Script
        if isinstance(script, str):
            raw = script.encode("utf-8", "surrogateescape")
        else:
            raw = bytes(script)
        if raw.startswith(b"RIFF") and raw[8:12] == b"FEV ":
            candidates.append((asset.m_Name, raw))
    if len(candidates) != 1:
        names = ", ".join(name for name, _ in candidates) or "无"
        raise ValueError(f"期望 bundle 内恰有一个 RIFF FEV TextAsset，实际：{names}")
    return candidates[0][1]


def load_event_paths(path: Path) -> dict[str, str]:
    result = {}
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event_guid, event_path = line.split("\t", 1)
        except ValueError as exc:
            raise ValueError(f"{path}:{line_no} 不是 GUID<TAB>path") from exc
        event_guid = event_guid.lower()
        if not re.fullmatch(r"[0-9a-f]{32}", event_guid):
            raise ValueError(f"{path}:{line_no} GUID 无效：{event_guid}")
        result[event_guid] = event_path
    return result


def parse_fev(blob: bytes) -> dict:
    lists = collect_lists(blob)

    def containers(name: bytes) -> list[Chunk]:
        found = lists.get(name, [])
        if not found:
            raise ValueError(f"FEV 缺少 LIST/{name.decode('ascii')}")
        return found

    events = {}
    for item in containers(b"EVNT"):
        payload = direct_payload(blob, item, b"EVTB")
        if len(payload) < 48:
            raise ValueError("EVTB 太短")
        events[guid(payload[:16])] = guid(payload[32:48])

    timelines = {}
    for item in containers(b"TMLN"):
        payload = direct_payload(blob, item, b"TLNB")
        if len(payload) < 20:
            raise ValueError("TLNB 太短")
        timeline_guid = guid(payload[:16])
        # Two FMOD 2.03.x variants exist in current BD2 banks:
        #   voice: GUID + count:u16 + width:u16 + records
        #   SFX:   GUID + type:u16 + count:u16 + width:u16 + records
        if u16(payload, 18) == 24:
            record_count = u16(payload, 16)
            record_width = u16(payload, 18)
            records_offset = 20
        elif len(payload) >= 22 and u16(payload, 20) == 24:
            record_count = u16(payload, 18)
            record_width = u16(payload, 20)
            records_offset = 22
        else:
            # Empty timelines use several short layouts and have no records.
            timelines[timeline_guid] = []
            continue
        if record_count % 2 != 1 or record_width != 24:
            raise ValueError(
                f"未知 TLNB 结构：guid={timeline_guid}, "
                f"count={record_count}, width={record_width}"
            )
        count = (record_count - 1) // 2
        expected = records_offset + count * record_width
        if len(payload) < expected:
            raise ValueError(f"TLNB 数据不完整：{timeline_guid}")
        refs = []
        for index in range(count):
            offset = records_offset + index * record_width
            refs.append(
                {
                    "instrument": guid(payload[offset : offset + 16]),
                    "startTicks": u32(payload, offset + 16),
                    "durationTicks": u32(payload, offset + 20),
                }
            )
        timelines[timeline_guid] = refs

    multi_instruments = {}
    for item in containers(b"MUIT"):
        instrument = direct_payload(blob, item, b"MUIB")
        playlist = direct_payload(blob, item, b"PLST")
        if len(instrument) < 16 or len(playlist) < 12:
            # Some BD2 SFX banks contain empty/placeholder MUIT containers.
            # They are safe to ignore unless a Timeline references them later,
            # in which case extraction still fails as an unknown instrument.
            continue
        instrument_guid = guid(instrument[:16])
        record_count = u16(playlist, 8)
        record_width = u16(playlist, 10)
        if record_count % 2 != 1 or record_width != 20:
            raise ValueError(
                f"未知 PLST 结构：guid={instrument_guid}, "
                f"count={record_count}, width={record_width}"
            )
        count = (record_count - 1) // 2
        expected = 12 + count * record_width
        if len(playlist) < expected:
            raise ValueError(f"PLST 数据不完整：{instrument_guid}")
        choices = []
        for index in range(count):
            offset = 12 + index * record_width
            choices.append(
                {
                    "wait": guid(playlist[offset : offset + 16]),
                    "weight": f32(playlist, offset + 16),
                }
            )
        multi_instruments[instrument_guid] = choices

    waits = {}
    for item in containers(b"WAIT"):
        payload = direct_payload(blob, item, b"WAIB")
        if len(payload) < 32:
            raise ValueError("WAIB 太短")
        waits[guid(payload[:16])] = guid(payload[16:32])

    waves = {}
    wavs_container = containers(b"WAVS")
    if len(wavs_container) != 1:
        raise ValueError(f"期望一个 WAVS，实际 {len(wavs_container)}")
    for child in iter_chunks(
        blob, wavs_container[0].payload_start, wavs_container[0].payload_end
    ):
        if child.tag != b"WAV ":
            continue
        payload = blob[child.payload_start : child.payload_end]
        if len(payload) < 26:
            raise ValueError("WAV chunk 太短")
        waves[guid(payload[:16])] = u32(payload, 22)

    project = containers(b"PROJ")
    if len(project) != 1:
        raise ValueError(f"期望一个 PROJ，实际 {len(project)}")
    bank_info = direct_payload(blob, project[0], b"BNKI")
    if len(bank_info) < 16:
        raise ValueError("BNKI 太短")

    return {
        "bankGuid": guid(bank_info[:16]),
        "events": events,
        "timelines": timelines,
        "multiInstruments": multi_instruments,
        "waits": waits,
        "waves": waves,
    }


def vgmstream_metadata(executable: Path, fsb: Path) -> dict[int, dict]:
    completed = subprocess.run(
        [str(executable), "-s", "1", "-S", "0", "-I", str(fsb)],
        check=True,
        capture_output=True,
        text=True,
    )
    result = {}
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        stream = item["streamInfo"]
        index = int(stream["index"]) - 1
        result[index] = {
            "name": stream["name"],
            "stream": index + 1,
            "sampleRate": item["sampleRate"],
            "channels": item["channels"],
            "samples": item["playSamples"],
            "duration": item["playSamples"] / item["sampleRate"],
            "encoding": item["encoding"],
        }
        looping = item.get("loopingInfo")
        if looping:
            result[index]["looping"] = looping
    return result


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._")
    if not cleaned:
        raise ValueError(f"无法生成安全文件名：{name!r}")
    return cleaned


def decode_ogg(
    vgmstream: Path,
    ffmpeg: Path,
    fsb: Path,
    stream: int,
    output: Path,
):
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bd2-voice-") as temp:
        wav = Path(temp) / "voice.wav"
        subprocess.run(
            [
                str(vgmstream),
                "-i",
                "-s",
                str(stream),
                "-o",
                str(wav),
                str(fsb),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        base_cmd = [
            str(ffmpeg),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(wav),
            "-ar",
            "48000",
        ]
        try:
            subprocess.run(
                [*base_cmd, "-c:a", "libvorbis", "-q:a", "4", str(output)],
                check=True,
            )
        except subprocess.CalledProcessError:
            # Some Homebrew/macOS FFmpeg builds expose the native Vorbis encoder
            # but not libvorbis. Native vorbis is good enough for browser OGG
            # delivery, so fall back instead of forcing a custom FFmpeg build.
            subprocess.run(
                [
                    *base_cmd,
                    "-ac",
                    "2",
                    "-strict",
                    "-2",
                    "-c:a",
                    "vorbis",
                    "-q:a",
                    "4",
                    str(output),
                ],
                check=True,
            )


def short_event_name(event_path: str, char_id: str, language: str) -> str | None:
    prefix = f"{char_id.capitalize()}_Int_"
    suffix = f"_{language}"
    basename = event_path.rsplit("/", 1)[-1]
    if not basename.startswith(prefix) or not basename.endswith(suffix):
        return None
    return basename[len(prefix) : -len(suffix)]


def short_event_name_from_sample(sample_name: str, char_id: str) -> str | None:
    """从 FSB stream 名反推事件短名。

    情绪型 interaction bank 的 SoundMaster 路径有时拿不到，但 FEV/FSB 的 wave
    名仍是 ``Char003303_Int_Smile1_1`` 这种结构。去掉末尾 sample 序号后即可
    得到和普通 event path 相同的短名 ``Smile1``。
    """
    prefix = f"{char_id.capitalize()}_Int_"
    if not sample_name.startswith(prefix):
        return None
    tail = sample_name[len(prefix) :]
    m = re.match(r"(.+)_\d+$", tail)
    return m.group(1) if m else tail


def round_seconds(ticks: int) -> float:
    return round(ticks / TIMELINE_TICKS_PER_SECOND, 6)


def build_character_data(
    graph: dict,
    paths: dict[str, str],
    metadata: dict[int, dict],
    dating_id: str,
    char_id: str,
    source_version: str,
    language: str,
    bundle_hash: str | None,
    bank_hash: str,
    fsb_hash: str,
    infer_event_paths_from_samples: bool = False,
    expect_events: int | None = None,
    expect_samples: int | None = None,
) -> dict:
    samples = {}
    events = {}
    actions = {}
    used_streams = set()
    skipped_waits: set[str] = set()
    skipped_waves: set[str] = set()

    for event_guid, timeline_guid in graph["events"].items():
        event_path = paths.get(event_guid)
        if event_path and event_path.endswith(f"_{language}"):
            name = short_event_name(event_path, char_id, language)
            if name is None:
                continue
        elif infer_event_paths_from_samples:
            event_path = None
            name = None
        else:
            continue

        triggers = []
        for ref in graph["timelines"].get(timeline_guid, []):
            instrument_guid = ref["instrument"]
            if instrument_guid in graph["multiInstruments"]:
                raw_choices = graph["multiInstruments"][instrument_guid]
            elif instrument_guid in graph["waits"]:
                raw_choices = [{"wait": instrument_guid, "weight": 100.0}]
            else:
                raise ValueError(
                    f"Timeline {timeline_guid} 引用了未知 instrument {instrument_guid}"
                )

            choices = []
            for choice in raw_choices:
                wav_guid = graph["waits"].get(choice["wait"])
                if wav_guid is None:
                    skipped_waits.add(choice["wait"])
                    continue
                stream_index = graph["waves"].get(wav_guid)
                if stream_index is None:
                    skipped_waves.add(wav_guid)
                    continue
                if stream_index not in metadata:
                    raise ValueError(f"FSB 缺少 stream index {stream_index}")
                sample = metadata[stream_index]
                sample_name = sample["name"]
                if name is None:
                    name = short_event_name_from_sample(sample_name, char_id)
                used_streams.add(stream_index)
                choices.append(
                    {
                        "sample": sample_name,
                        "weight": round(choice["weight"], 6),
                    }
                )
                samples[sample_name] = {
                    **sample,
                    "file": f"{safe_filename(sample_name)}.ogg",
                }
            if choices:
                triggers.append(
                    {
                        "at": round_seconds(ref["startTicks"]),
                        "window": round_seconds(ref["durationTicks"]),
                        "choices": choices,
                    }
                )

        if name is None:
            continue
        triggers.sort(key=lambda item: item["at"])
        events[name] = {
            "guid": event_guid,
            "path": event_path or (
                f"event:/Voices/Common/{char_id.capitalize()}/Interaction/"
                f"{char_id.capitalize()}_Int_{name}_{language}"
            ),
            **({"pathInferredFromSamples": True} if event_path is None else {}),
            "triggers": triggers,
        }
        if re.match(r"^(?:mix|motion)\d+_", name):
            actions[name] = name

    if expect_events is not None and len(events) != expect_events:
        raise ValueError(
            f"预期 {language} 语音事件 {expect_events} 个，实际 {len(events)}"
        )
    if expect_samples is not None and len(used_streams) != expect_samples:
        raise ValueError(
            f"预期引用 {expect_samples} 个 sample，实际 {len(used_streams)}"
        )
    if skipped_waits:
        print(
            "warning: 跳过未知 WAIT 候选 "
            f"{len(skipped_waits)} 个：{', '.join(sorted(skipped_waits)[:8])}",
            file=sys.stderr,
        )
    if skipped_waves:
        print(
            "warning: 跳过未知 WAV 候选 "
            f"{len(skipped_waves)} 个：{', '.join(sorted(skipped_waves)[:8])}",
            file=sys.stderr,
        )

    return {
        "charId": char_id,
        "sourceVersion": source_version,
        "language": language,
        "audioBase": f"./audio/dating/{dating_id}/voice/",
        "bank": {
            "guid": graph["bankGuid"],
            "bundleSha256": bundle_hash,
            "bankSha256": bank_hash,
            "fsbSha256": fsb_hash,
            "codec": "FMOD FADPCM",
        },
        "samples": dict(sorted(samples.items())),
        "events": dict(sorted(events.items())),
        "actions": dict(sorted(actions.items())),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--bundle", type=Path, help="interaction voice Unity bundle")
    source.add_argument("--bank", type=Path, help="已解出的 RIFF FEV bank")
    parser.add_argument("--fsb", type=Path, required=True, help="bank 内嵌 FSB5")
    parser.add_argument(
        "--event-paths",
        type=Path,
        required=True,
        help="Master.strings 导出的 GUID<TAB>event path",
    )
    parser.add_argument(
        "--infer-event-paths-from-samples",
        action="store_true",
        help="当 event-paths 缺失目标事件时，从 FSB stream 名反推情绪事件名。",
    )
    parser.add_argument("--dating-id", required=True, help="例如 illust_dating18")
    parser.add_argument("--char-id", required=True, help="例如 char000396")
    parser.add_argument("--source-version", required=True)
    parser.add_argument(
        "--language",
        default="KR",
        help="项目默认统一使用 KR",
    )
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
    parser.add_argument(
        "--output-data",
        type=Path,
        default=ROOT / "data" / "dating_audio.json",
    )
    parser.add_argument("--audio-dir", type=Path)
    parser.add_argument(
        "--decode",
        action="store_true",
        help="将当前语言引用的所有 sample 转为 OGG",
    )
    parser.add_argument(
        "--expect-events",
        type=int,
        help="可选验收断言：期望当前语言事件数",
    )
    parser.add_argument(
        "--expect-samples",
        type=int,
        help="可选验收断言：期望当前语言引用 sample 数",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    fsb = args.fsb.resolve()
    if not fsb.is_file():
        raise SystemExit(f"FSB 不存在：{fsb}")
    if not args.vgmstream.is_file() and shutil.which(str(args.vgmstream)) is None:
        raise SystemExit(f"vgmstream-cli 不存在：{args.vgmstream}")

    if args.bundle:
        bundle = args.bundle.resolve()
        bank_blob = extract_bank(bundle)
        bundle_hash = sha256(bundle)
    else:
        bundle = None
        bank_blob = args.bank.resolve().read_bytes()
        bundle_hash = None

    graph = parse_fev(bank_blob)
    paths = load_event_paths(args.event_paths.resolve())
    metadata = vgmstream_metadata(args.vgmstream, fsb)
    bank_hash = hashlib.sha256(bank_blob).hexdigest()
    character = build_character_data(
        graph=graph,
        paths=paths,
        metadata=metadata,
        dating_id=args.dating_id,
        char_id=args.char_id,
        source_version=args.source_version,
        language=args.language,
        bundle_hash=bundle_hash,
        bank_hash=bank_hash,
        fsb_hash=sha256(fsb),
        infer_event_paths_from_samples=args.infer_event_paths_from_samples,
        expect_events=args.expect_events,
        expect_samples=args.expect_samples,
    )

    output = args.output_data.resolve()
    if output.exists():
        document = json.loads(output.read_text(encoding="utf-8"))
    else:
        document = {"version": 1, "characters": {}}
    if document.get("version") != 1 or not isinstance(document.get("characters"), dict):
        raise ValueError(f"无法合并未知格式：{output}")
    existing = document["characters"].get(args.dating_id)
    if existing and "sfx" in existing:
        character["sfx"] = existing["sfx"]
    if existing and "interactionVoices" in existing:
        character["interactionVoices"] = existing["interactionVoices"]
    document["characters"][args.dating_id] = character
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    audio_dir = (
        args.audio_dir.resolve()
        if args.audio_dir
        else ROOT / "audio" / "dating" / args.dating_id / "voice"
    )
    if args.decode:
        audio_dir.mkdir(parents=True, exist_ok=True)
        samples = sorted(character["samples"].values(), key=lambda item: item["stream"])
        for index, sample in enumerate(samples, 1):
            target = audio_dir / sample["file"]
            print(
                f"[{index:03d}/{len(samples):03d}] "
                f"{sample['name']} -> {target.name}"
            )
            decode_ogg(
                args.vgmstream,
                args.ffmpeg,
                fsb,
                sample["stream"],
                target,
            )

    trigger_count = sum(
        len(event["triggers"]) for event in character["events"].values()
    )
    action_count = len(character["actions"])
    print(
        f"完成：{len(character['events'])} 个 {args.language} 事件，"
        f"{trigger_count} 个时间触发点，{action_count} 个动作映射，"
        f"{len(character['samples'])} 个 sample"
    )
    print(f"数据：{output}")
    if args.decode:
        print(f"音频：{audio_dir}")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f"外部命令失败（exit {exc.returncode}）：{exc.cmd}", file=sys.stderr)
        raise SystemExit(exc.returncode)
