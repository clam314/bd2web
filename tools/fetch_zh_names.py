#!/usr/bin/env python3
"""抓取 gamekee 官方中文角色名/服装名，输出 data/zh.json。

数据通路（均需 gamekee 防盗链请求头）：
  1. 词条树 https://www.gamekee.com/v1/wiki/entry  → 角色/物品图鉴 下 5/4/3 星角色，
     每个 child 含中文名(name) 与页面 id(content_id)
  2. 单页内容 https://api-cdn.gamekee.com/wiki2.0/pro/50118/content/<id>.json
     content 是嵌套 JSON；每个「皮肤N」模块内 charXXXXYY 反推 costumeId，
     模块里 "服装名称"/"简中服装名称" 字段后跟的文本即官方中文服装名

输出 data/zh.json: {"chars": {"0675": "卢班希亚"}, "costumes": {"067502": "印鉴掠夺者"}}
失败的页面跳过（保留已有结果），可重复运行。
"""
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "zh.json"
HDR = {"Referer": "https://www.gamekee.com/zsca2/", "game-alias": "zsca2",
       "User-Agent": "Mozilla/5.0"}
ENTRY_URL = "https://www.gamekee.com/v1/wiki/entry"
CONTENT_URL = "https://api-cdn.gamekee.com/wiki2.0/pro/50118/content/{}.json"


def http_json(url, headers, tries=2):
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # 网络抖动重试一次即可，不死磕
            last = e
            time.sleep(1)
    raise last


def list_characters():
    """返回 [(中文名, 页面id)]，覆盖 5/4/3 星角色。"""
    data = http_json(ENTRY_URL, HDR)["data"]
    chars = []
    for top in data.get("entry_list", []):
        if top.get("name") != "角色/物品图鉴":
            continue
        for cat in top.get("child") or []:
            if cat.get("name") not in ("5星角色", "4星角色", "3星角色"):
                continue
            for ch in cat.get("child") or []:
                pid = ch.get("content_id") or ch.get("id")
                if ch.get("name") and pid:
                    chars.append((ch["name"], pid))
    return chars


def _texts_in_order(node, acc):
    if isinstance(node, dict):
        if node.get("type") == "text":
            acc.append(node.get("value", ""))
        for v in node.values():
            _texts_in_order(v, acc)
    elif isinstance(node, list):
        for v in node:
            _texts_in_order(v, acc)


def _modules(node):
    """yield 每个带 title/name 的模块节点。"""
    if isinstance(node, dict):
        if node.get("title") or node.get("name"):
            yield node
        for v in node.values():
            yield from _modules(v)
    elif isinstance(node, list):
        for v in node:
            yield from _modules(v)


def parse_page(page_json):
    """从单页内容解析 {costumeId: 中文服装名} 与该页的 charId(4位)。"""
    content = page_json.get("data", page_json)
    content = content.get("content", content) if isinstance(content, dict) else content
    if isinstance(content, str):
        content = json.loads(content)

    costumes = {}
    char_id = None
    seen = set()
    for mod in _modules(content):
        s = json.dumps(mod, ensure_ascii=False)
        m = re.search(r"char(\d{6})", s)
        if not m:
            continue
        costume_id = m.group(1)
        if costume_id in seen:
            continue
        seen.add(costume_id)
        char_id = char_id or costume_id[:4]
        ts = []
        _texts_in_order(mod, ts)
        for i, t in enumerate(ts):
            if t in ("服装名称", "简中服装名称") and i + 1 < len(ts):
                name = ts[i + 1].strip()
                if name and name not in ("服装定位", "服装类型"):
                    costumes[costume_id] = name
                break
    return char_id, costumes


def main():
    chars_out, costumes_out = {}, {}
    roster = list_characters()
    print(f"角色页面: {len(roster)}", file=sys.stderr)
    for i, (name, pid) in enumerate(roster, 1):
        try:
            page = http_json(CONTENT_URL.format(pid), {"Referer": "https://www.gamekee.com/"})
            cid, costumes = parse_page(page)
            if cid:
                chars_out[cid] = name
                costumes_out.update(costumes)
            print(f"[{i}/{len(roster)}] {name} (char {cid}) +{len(costumes)} 服装", file=sys.stderr)
        except Exception as e:
            print(f"[{i}/{len(roster)}] {name} 跳过：{e}", file=sys.stderr)
        time.sleep(0.2)

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(
        {"chars": chars_out, "costumes": costumes_out},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"zh.json: {len(chars_out)} 角色名, {len(costumes_out)} 服装名 -> {OUT}")


if __name__ == "__main__":
    main()
