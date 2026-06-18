#!/usr/bin/env python3
"""从 APK bundle 解 cutscene 的真实运镜/调色/取景关键帧到 data/cutscene_shots.json。

数据来自 Unity Timeline 烘出来的 AnimationClip（StreamedClip 二进制），按
AssetStudio 的格式手解。每个 cutscene bundle 出 1 条记录：
  {
    "_hash": "<bundle hash from file.json>",  # 增量 key
    "duration": 8.883,
    "tracks": {                               # 真值连续曲线（线性插值）
       "Anchors.AnchoredX": [[t,v], ...],
       "Anchors/object.AnchoredX": [...],
       ...
    },
    "events": [                               # 离散 on/off（硬切）
       [t, "Bg_A", true],
       [t, "PostProcessVolume", false],
       ...
    ]
  }

增量提取：file.json 里 bundle 的 `hash` 字段是游戏内容的指纹，
我们存到记录的 `_hash`，下次跑时同 hash 就跳过。游戏更新只会重新
处理变了的角色。

用法：python3 tools/extract_cutscene_shots.py [--force]
"""
import argparse
import json
import re
import struct
import sys
import time
import zlib
from pathlib import Path

import UnityPy

UnityPy.config.FALLBACK_UNITY_VERSION = "2021.3.40f1"

ROOT = Path(__file__).resolve().parent.parent
BACKUP = Path("/Users/woods/bd2_gamedata_backup")
CACHE = BACKUP / "UnityCache" / "Shared"
FILE_JSON = BACKUP / "addressables" / "file.json"
OUT = ROOT / "data" / "cutscene_shots.json"

# Unity attribute 哈希 → 可读名（从已知典型对比中确认）
ATTR_NAMES = {
    1: "LocalPos.x", 2: "LocalPos.y", 3: "LocalPos.z",
    538195251: "AnchoredX",
    1460864421: "AnchoredY",
    2086281974: "IsActive",
}
# 我们关心的属性：相机/取景平移、IsActive 硬切
TRACK_ATTRS = {538195251, 1460864421, 1, 2, 3}      # 位置/锚点（连续插值）
EVENT_ATTR = 2086281974                              # IsActive（离散）

CUTSCENE_RE = re.compile(r"isolated-cutscene(\d{6})-group")


def bundle_data_path(bundle_hash):
    """UnityCache/Shared/<bundleHash>/<innerHash>/__data。"""
    outer = CACHE / bundle_hash
    if not outer.is_dir():
        return None
    for inner in outer.iterdir():
        data = inner / "__data"
        if data.is_file():
            return data
    return None


def decode_streamed(data_u32):
    """按 AssetStudio 的 StreamedClip 格式解：frame = (time float, n int, n×(idx int, c0..3 float))。
    value 取 c[3]（每帧 key 的真值），切线信息丢弃——线性插值在前端做。
    第一个 frame 的 time 是 -3.4e38（哨兵），保存 curve 的 t=0 初始值；后续 frame 是真实时间。
    我们把哨兵 frame 改写为 t=0，这样前端在 t=0 取值就拿到正确的起点（不会读到 timeline 末段"飞出屏幕"的大数值）。
    """
    buf = b"".join(struct.pack("<I", v) for v in data_u32)
    frames, off = [], 0
    is_first = True
    while off + 8 <= len(buf):
        t = struct.unpack_from("<f", buf, off)[0]; off += 4
        n = struct.unpack_from("<i", buf, off)[0]; off += 4
        if n < 0 or n > 1000 or off + n * 20 > len(buf):
            break
        keys = []
        for _ in range(n):
            idx = struct.unpack_from("<i", buf, off)[0]; off += 4
            c = struct.unpack_from("<4f", buf, off); off += 16
            keys.append((idx, c[3]))
        # 把哨兵 frame 视为 t=0 初始值（curve 的开口值）
        if is_first and t < -1e30:
            t = 0.0
        frames.append((t, keys))
        is_first = False
    return frames


# 路径归一化：不同角色的 hierarchy 深度不同（有的角色多套了 Cut/CutN 层级），
# 我们要把根节点 + 中间包装层砍掉，只保留从第一个"关键节点"开始的相对路径，
# 这样跨角色对齐才有意义。还要区分主阶段 / loop / loop_2…（同名节点但属于不同阶段）。
KEEP_PREFIXES = ("Bg_", "bg ", "PostProcessVolume", "UIParticle")
PHASE_RE = re.compile(r"^CutScene\d+(_loop(?:_\d+)?)?")


def shortpath(p):
    parts = p.split("/")
    if not parts:
        return None
    m = PHASE_RE.match(parts[0])
    phase = ""
    if m:
        # _loop / _loop_2 后缀作为阶段名；主阶段为 ""（不加前缀）
        phase = (m.group(1) or "").lstrip("_")
    # 找第一个关键节点（Anchors / Bg_* / PostProcessVolume* / UIParticle*）
    for i in range(1, len(parts)):
        x = parts[i]
        if x == "Anchors" or x.startswith(KEEP_PREFIXES):
            short = "/".join(parts[i:])
            return f"{phase}:{short}" if phase else short
    return None


def extract_one(data_path):
    """从一个 cutscene bundle 文件解出运镜数据。"""
    env = UnityPy.load(str(data_path))

    # 1) 建 GameObject 路径表（pathCRC → 节点路径），用于把 binding 的 path 反解
    gos, tfs = {}, {}
    for o in env.objects:
        if o.type.name == "GameObject":
            d = o.read_typetree()
            gos[o.path_id] = d.get("m_Name", "?")
        elif o.type.name in ("Transform", "RectTransform"):
            d = o.read_typetree()
            tfs[o.path_id] = {
                "go": d["m_GameObject"]["m_PathID"],
                "parent": d.get("m_Father", {}).get("m_PathID", 0),
            }

    def path_of(tfid):
        parts = []
        while tfid:
            t = tfs.get(tfid)
            if not t:
                break
            parts.append(gos.get(t["go"], "?"))
            if t["parent"] == 0:
                break
            tfid = t["parent"]
        return "/".join(reversed(parts))

    crc_map = {}
    for tfid in tfs:
        p = path_of(tfid)
        if not p:
            continue
        # Unity 在 AnimationClip 里存的是相对路径——根名通常不算，但稳起见把几种变体都注册
        for v in (p, "/".join(p.split("/")[1:]), p.split("/")[-1]):
            if v:
                crc_map[zlib.crc32(v.encode("utf-8")) & 0xFFFFFFFF] = p

    # 2) 解所有 AnimationClip（同 bundle 通常有 2 份重复，合并去重）
    tracks = {}    # "path.attr" → [[t,v],...]
    events = []    # [t, path_name, bool]
    duration = 0.0

    for obj in env.objects:
        if obj.type.name != "AnimationClip":
            continue
        d = obj.read_typetree()
        duration = max(duration, d["m_MuscleClip"]["m_StopTime"])
        bindings = d["m_ClipBindingConstant"]["genericBindings"]
        sc = d["m_MuscleClip"]["m_Clip"]["data"]["m_StreamedClip"]
        frames = decode_streamed(sc["data"])

        # 反汇编每个 binding 的 keys
        for cidx, b in enumerate(bindings):
            attr = b["attribute"]
            if attr not in TRACK_ATTRS and attr != EVENT_ATTR:
                continue
            path = crc_map.get(b["path"])
            if not path:
                continue
            short = shortpath(path)
            if not short:
                continue
            keys = [(t, v) for t, keys in frames for kidx, v in keys
                    if kidx == cidx and t > -1e30]
            if not keys:
                continue
            if attr == EVENT_ATTR:
                for t, v in keys:
                    events.append([round(t, 4), short, v > 0.5])
            else:
                k = f"{short}.{ATTR_NAMES.get(attr, str(attr))}"
                # 合并两份 clip 中的相同 track（如重复就去重）
                existing = tracks.get(k, [])
                merged = sorted(set((round(t, 4), round(v, 3)) for t, v in keys + [(t, v) for t, v in existing]))
                tracks[k] = [[t, v] for t, v in merged]

    # 事件去重 & 按时间排序
    events = sorted({(t, p, v) for t, p, v in events})
    events = [[t, p, v] for t, p, v in events]

    return {
        "duration": round(duration, 4),
        "tracks": tracks,
        "events": events,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="忽略缓存，全量重跑")
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 个（调试用）")
    args = ap.parse_args()

    file_json = json.loads(FILE_JSON.read_text())
    # 列出所有 cutscene bundle 及其 hash
    targets = []
    for b in file_json.get("bundles", []):
        m = CUTSCENE_RE.match(b.get("readableName", ""))
        if not m:
            continue
        targets.append({
            "char": m.group(1),
            "bundleName": b["bundleName"],
            "hash": b["hash"],
        })
    targets.sort(key=lambda x: x["char"])
    if args.limit:
        targets = targets[:args.limit]
    print(f"发现 {len(targets)} 个 cutscene bundle")

    # 加载已有 JSON，做增量
    if OUT.exists() and not args.force:
        existing = json.loads(OUT.read_text())
    else:
        existing = {"version": file_json.get("version"), "extracted_at": "", "characters": {}}
    chars = existing.setdefault("characters", {})

    new, skip, fail = 0, 0, 0
    for tgt in targets:
        cid = tgt["char"]
        prev = chars.get(cid)
        if prev and prev.get("_hash") == tgt["hash"] and not args.force:
            skip += 1
            continue
        dp = bundle_data_path(tgt["bundleName"])
        if not dp:
            print(f"  {cid}: ⚠ bundle 文件不在本地缓存，跳过")
            fail += 1
            continue
        try:
            rec = extract_one(dp)
            rec["_hash"] = tgt["hash"]
            chars[cid] = rec
            n_tracks = len(rec["tracks"])
            n_events = len(rec["events"])
            print(f"  {cid}: ✓ duration={rec['duration']}s tracks={n_tracks} events={n_events}")
            new += 1
        except Exception as e:
            print(f"  {cid}: ✗ {e}")
            fail += 1

    existing["version"] = file_json.get("version")
    existing["extracted_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
    print(f"\n完成：新提取 {new}，缓存命中 {skip}，失败 {fail}，写入 {OUT}")


if __name__ == "__main__":
    main()
