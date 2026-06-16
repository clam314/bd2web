#!/usr/bin/env python3
"""从备份的游戏资源里提取每套服装的技能动画背景到 bg/<costumeId>_<N>.png。

游戏每个 cutscene bundle 里直接带 char<costumeId>_back1 / _back2 这类 Texture2D，
这就是游戏的真实场景背景（蓝天、街道等），命名按服装编号，映射零成本。

用法：python3 tools/extract_bgs.py
    扫 /Users/woods/bd2_gamedata_backup/ 下所有 isolated-cutsceneXXXXXX 包，
    导出到本仓库 bg/<costumeId>_<N>.png（N 为 1/2，对应技能动画 1/2）。
"""
import json
import re
import sys
from pathlib import Path

import UnityPy

UnityPy.config.FALLBACK_UNITY_VERSION = "2021.3.40f1"

ROOT = Path(__file__).resolve().parent.parent
BACKUP = Path("/Users/woods/bd2_gamedata_backup")
CACHE = BACKUP / "UnityCache" / "Shared"
OUT = ROOT / "bg"

PATTERN = re.compile(r"^char(\d{6})_back(\d+)$")


def bundle_data_path(bundle_hash):
    """UnityCache/Shared/<bundleHash>/<innerHash>/__data 的内层是随机命名目录，找它。"""
    outer = CACHE / bundle_hash
    if not outer.is_dir():
        return None
    for inner in outer.iterdir():
        data = inner / "__data"
        if data.is_file():
            return data
    return None


def main():
    OUT.mkdir(exist_ok=True)
    catalog = json.loads((BACKUP / "addressables" / "file.json").read_text())
    cuts = [b for b in catalog["bundles"]
            if b.get("readableName", "").startswith("isolated-cutscene")]

    found, missing, exported = 0, 0, 0
    for b in cuts:
        data = bundle_data_path(b["bundleName"])
        if not data:
            missing += 1
            continue
        try:
            env = UnityPy.load(str(data))
        except Exception as e:
            print(f"[{b['readableName']}] 加载失败: {e}", file=sys.stderr)
            continue
        for o in env.objects:
            if o.type.name != "Texture2D":
                continue
            try:
                d = o.read()
                m = PATTERN.match(d.m_Name)
                if not m:
                    continue
                costume_id, idx = m.group(1), m.group(2)
                # 只要 1024x1024 整张（避免分块版 back1-1/back1-2 这类小图）
                if (d.m_Width, d.m_Height) != (1024, 1024):
                    continue
                out = OUT / f"{costume_id}_{idx}.png"
                if out.exists():
                    continue
                d.image.save(out)
                exported += 1
            except Exception as e:
                print(f"  texture err: {e}", file=sys.stderr)
        found += 1

    print(f"扫描 cutscene 包 {found} 个（{missing} 个未在本地缓存），新导出 {exported} 张背景 -> {OUT}")
    # 统计
    files = sorted(OUT.glob("*.png"))
    costumes = {f.stem.split("_")[0] for f in files}
    print(f"现有 bg 文件 {len(files)} 张，覆盖 {len(costumes)} 套服装")


if __name__ == "__main__":
    main()
