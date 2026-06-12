#!/usr/bin/env python3
"""生成 data/roster.json（人物 → 服装 → 素材路径）。

两种模式：
  默认        扫描本地 upstream/ 目录（tools/sync.sh 克隆的素材）
  --remote    不需要本地素材：通过 GitHub API 拉上游文件清单（Actions 用，几秒完成）

目录命名规律：
  spine/char/char<AAAA><BB>/               AAAA=角色编号 BB=服装序号（待机模型）
  spine/cutscenes/cutscene_char<AAAA><BB>/ 对应服装的 cutscene
角色/服装名来自上游 CharInfo(Dropped).json（有语法错误，做容错修复）。
"""
import json
import re
import subprocess
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = ROOT / "upstream"
OUT = ROOT / "data" / "roster.json"
REPO = "myssal/Brown-Dust-2-Asset"

DIR_RE = re.compile(r"^char(\d{4})(\d{2,3})$")


def http_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "bd2web-roster"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def parse_charinfo(raw):
    """容错解析角色名映射。返回 ({costumeId: costumeName}, {charId: charName})。"""
    costume_names, char_names = {}, {}
    # 修复缺失逗号：一行以字符串值结尾、下一行直接开始新 key 的情况
    raw = re.sub(r'"\n(\s*")', '",\n\\1', raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"warn: CharInfo 解析失败（{e}），全部使用编号作为名字", file=sys.stderr)
        return costume_names, char_names
    for char in data:
        if char.get("charId") and char.get("charName"):
            char_names[char["charId"]] = char["charName"]
        for c in char.get("costumes", []):
            if c.get("costumeId") and c.get("costumeName"):
                costume_names[c["costumeId"]] = c["costumeName"]
    return costume_names, char_names


def load_local():
    """返回 (文件路径列表[相对 upstream], charinfo 文本, commit)。"""
    if not (UPSTREAM / "spine").is_dir():
        sys.exit("错误：upstream/spine 不存在，先运行 tools/sync.sh（或改用 --remote）")
    paths = [str(p.relative_to(UPSTREAM)) for p in (UPSTREAM / "spine").rglob("*") if p.is_file()]
    info_path = UPSTREAM / "CharInfo(Dropped).json"
    charinfo = info_path.read_text(encoding="utf-8") if info_path.exists() else ""
    commit = subprocess.run(["git", "-C", str(UPSTREAM), "rev-parse", "--short=12", "HEAD"],
                            capture_output=True, text=True).stdout.strip()
    return paths, charinfo, commit


def load_remote():
    head = http_json(f"https://api.github.com/repos/{REPO}/commits/master")
    commit = head["sha"][:12]
    root = http_json(f"https://api.github.com/repos/{REPO}/git/trees/{head['sha']}")
    spine_sha = next(t["sha"] for t in root["tree"] if t["path"] == "spine")
    tree = http_json(f"https://api.github.com/repos/{REPO}/git/trees/{spine_sha}?recursive=1")
    if tree.get("truncated"):
        sys.exit("错误：上游目录树超过 API 上限被截断，需改用克隆方式")
    paths = ["spine/" + t["path"] for t in tree["tree"] if t["type"] == "blob"]
    req = urllib.request.Request(
        f"https://raw.githubusercontent.com/{REPO}/{head['sha']}/CharInfo(Dropped).json",
        headers={"User-Agent": "bd2web-roster"})
    with urllib.request.urlopen(req, timeout=60) as r:
        charinfo = r.read().decode("utf-8")
    return paths, charinfo, commit


def find_spine_files(files_in_dir, dirpath):
    """在一个目录的文件名集合里找骨骼+图集。返回 (skeleton, atlas) 相对路径或 None。"""
    atlases = sorted(f for f in files_in_dir if f.endswith(".atlas"))
    if not atlases:
        return None
    atlas = atlases[0]
    stem = atlas[: -len(".atlas")]
    # 常规命名：x.atlas + x.skel；兼容 x.skel.atlas + x.skel.json 这类双后缀
    for ext in (".skel", ".json"):
        if stem + ext in files_in_dir:
            return (f"{dirpath}/{stem}{ext}", f"{dirpath}/{atlas}")
    others = sorted(f for f in files_in_dir if f.endswith((".skel", ".json")))
    if others:
        return (f"{dirpath}/{others[0]}", f"{dirpath}/{atlas}")
    return None


def main():
    remote = "--remote" in sys.argv
    paths, charinfo_raw, commit = load_remote() if remote else load_local()
    costume_names, char_names = parse_charinfo(charinfo_raw)

    # 按目录分组文件名
    dirs = defaultdict(set)
    for p in paths:
        d, _, fname = p.rpartition("/")
        dirs[d].add(fname)

    chars = {}

    for d in sorted(dirs):
        parts = d.split("/")
        if len(parts) != 3 or parts[0] != "spine":
            continue
        section, dirname = parts[1], parts[2]
        if section == "char":
            m = DIR_RE.match(dirname)
            kind, anim, suffix = "idle", "idle", ""
        elif section == "cutscenes" and dirname.startswith("cutscene_"):
            m = DIR_RE.match(dirname[len("cutscene_"):])
            kind, anim, suffix = "cutscene", "loop", " · Cutscene"
        else:
            continue
        if not m:
            continue  # 不符合命名规律（如 _c 审查版）跳过
        files = find_spine_files(dirs[d], d)
        if not files:
            continue
        cid, costume_id = m.group(1), m.group(1) + m.group(2)
        entry = chars.setdefault(cid, {
            "id": cid,
            "name": char_names.get(cid, f"Char {cid}"),
            "costumes": [],
        })
        label = costume_names.get(costume_id, f"服装 {costume_id[4:]}") + suffix
        entry["costumes"].append({
            "label": label, "kind": kind,
            "skeleton": files[0], "atlas": files[1],
            "anim": anim,
        })

    roster = sorted(chars.values(), key=lambda c: c["id"])
    for c in roster:
        c["costumes"].sort(key=lambda x: (x["kind"] != "idle", x["skeleton"]))

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": f"{REPO.split('/')[1]}@{commit}",
        "commit": commit,
        "characters": roster,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    n = sum(len(c["costumes"]) for c in roster)
    print(f"roster.json: {len(roster)} characters, {n} costumes, upstream@{commit} -> {OUT}")


if __name__ == "__main__":
    main()
