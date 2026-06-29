#!/usr/bin/env python3
"""从 BD2 的 common-char-datingillust bundle 提取约会角色 Spine 素材(.skel/.atlas/贴图)。

源 bundle 是标准 UnityFS(无加密),版本号被抹成 0.0.0 需指定 FALLBACK。
设备缓存路径示例:
  /sdcard/Android/data/com.neowizgames.game.browndust2/files/UnityCache/Shared/
    <bundleName>/<hash>/__data
  (bundleName 见 com.unity.addressables/file.json 里 readableName=common-char-datingillust_assets_all)

用法:
  python tools/extract_dating_spine.py <bundle> [out_dir]
  out_dir 默认 upstream/spine/illust/illust_dating
每角色输出 <out>/<id>/<id>.skel + <id>.atlas + atlas 引用的各贴图页 PNG。
"""
import sys, os, re, collections

def script_bytes(ta):
    s = ta.m_Script
    return s.encode("utf-8", "surrogateescape") if isinstance(s, str) else bytes(s)

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    bundle = sys.argv[1]
    out_base = sys.argv[2] if len(sys.argv) > 2 else "upstream/spine/illust/illust_dating"
    import UnityPy
    UnityPy.config.FALLBACK_UNITY_VERSION = "2021.3.40f1"
    env = UnityPy.load(bundle)

    texts = {}          # name -> TextAsset data
    textures = {}       # name -> Texture2D data
    for o in env.objects:
        try:
            d = o.read()
        except Exception:
            continue
        nm = getattr(d, "m_Name", "")
        if not nm:
            continue
        if o.type.name == "TextAsset":
            texts[nm] = d
        elif o.type.name == "Texture2D":
            textures[nm] = d

    ids = sorted({m.group(0) for n in texts if (m := re.fullmatch(r"illust_dating\d+", n.replace(".skel", "").replace(".atlas", "")))},
                 key=lambda x: int(x.replace("illust_dating", "")))
    print(f"发现 {len(ids)} 个约会角色: {', '.join(ids)}")

    summary = []
    for cid in ids:
        skel_ta = texts.get(f"{cid}.skel")
        atlas_ta = texts.get(f"{cid}.atlas")
        if not skel_ta or not atlas_ta:
            print(f"  [跳过] {cid}: 缺 skel/atlas"); continue
        d = os.path.join(out_base, cid)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, f"{cid}.skel"), "wb") as f:
            f.write(script_bytes(skel_ta))
        atlas_txt = atlas_ta.m_Script if isinstance(atlas_ta.m_Script, str) else script_bytes(atlas_ta).decode("utf-8", "replace")
        with open(os.path.join(d, f"{cid}.atlas"), "w", newline="\n") as f:
            f.write(atlas_txt)
        # atlas 里 .png 结尾的行 = 贴图页
        pages = [ln.strip() for ln in atlas_txt.splitlines() if ln.strip().endswith(".png")]
        ok, miss = 0, []
        for pg in pages:
            tname = pg[:-4]  # 去 .png
            tex = textures.get(tname)
            if tex is None:
                miss.append(pg); continue
            try:
                tex.image.save(os.path.join(d, pg)); ok += 1
            except Exception as e:
                miss.append(f"{pg}({e})")
        # skel 版本号
        sb = script_bytes(skel_ta)
        ver = re.search(rb"\d+\.\d+\.\d+", sb[:64])
        summary.append((cid, len(pages), ok, ver.group(0).decode() if ver else "?", miss))
        print(f"  [{cid}] spine={summary[-1][3]} 贴图 {ok}/{len(pages)}" + (f"  缺:{miss}" if miss else ""))

    print(f"\n完成,输出到 {out_base}/")
    bad = [s for s in summary if s[4] or s[2] != s[1]]
    if bad:
        print("⚠️ 有缺页:", [(s[0], s[4]) for s in bad])
    else:
        print("✅ 全部角色贴图齐全")

if __name__ == "__main__":
    main()
