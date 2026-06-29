#!/usr/bin/env python3
"""从心契 prefab 导出相对 SkeletonGraphic 的互动热区坐标。

旧版 `PREFAB_HOTZONES` 多数是沿 RectTransform 父链算到 Illust_dating 根画布
的 root-space 坐标。前端实际投影时用的是 SpinePlayer 暴露的 skeleton world
坐标，两者中间会隔着 `Parent`/`SkeletonGraphic` 的缩放，导致不同角色要手工补
`HOTZONE_WORLD_SCALES`。

本脚本复用莎拉坐标修正的证据路线：把 `_interactionBoxZoneRectTransform`
或 `_rectTransform` 直接换算到对应 `SkeletonGraphic (illust_datingX)`
坐标系。生成的坐标可在前端标记 `space: "skeleton"`，从而不再需要按角色猜 scale。
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import UnityPy


ROOT = Path(__file__).resolve().parent.parent
UnityPy.config.FALLBACK_UNITY_VERSION = "2021.3.40f1"


def refid(ref):
    if not ref:
        return None
    return (
        getattr(ref, "path_id", None)
        or (ref.get("m_PathID") if isinstance(ref, dict) else None)
        or (ref.get("path_id") if isinstance(ref, dict) else None)
    )


def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def transform(m, x, y):
    return m[0][0] * x + m[0][1] * y + m[0][2], m[1][0] * x + m[1][1] * y + m[1][2]


def load_bundle(path: Path):
    env = UnityPy.load(str(path))
    game_objects = {}
    components = {}
    rects = {}
    monos = {}

    for obj in env.objects:
        if obj.type.name == "GameObject":
            data = obj.read_typetree()
            game_objects[obj.path_id] = data
            components[obj.path_id] = [
                refid(item.get("component") or item.get("m_Component"))
                for item in data.get("m_Component", [])
            ]
        elif obj.type.name == "RectTransform":
            rects[obj.path_id] = obj.read_typetree()
        elif obj.type.name == "MonoBehaviour":
            try:
                monos[obj.path_id] = obj.read_typetree()
            except Exception:
                pass

    return game_objects, components, rects, monos


def build_helpers(game_objects, components, rects):
    comp_go = {component: go for go, items in components.items() for component in items}

    def go_name(go):
        return game_objects.get(go, {}).get("m_Name")

    def rect_of_go(go):
        for component in components.get(go, []):
            if component in rects:
                return component
        return None

    def go_of_rect(rect):
        return comp_go.get(rect)

    def parent(rect):
        return refid(rects[rect].get("m_Father"))

    def pos(rect):
        value = rects[rect].get("m_AnchoredPosition") or {}
        return float(value.get("x", 0)), float(value.get("y", 0))

    def size(rect):
        value = rects[rect].get("m_SizeDelta") or {}
        return float(value.get("x", 0)), float(value.get("y", 0))

    def local_scale(rect):
        value = rects[rect].get("m_LocalScale") or {}
        return float(value.get("x", 1)), float(value.get("y", 1))

    def pivot(rect):
        value = rects[rect].get("m_Pivot") or {}
        return float(value.get("x", 0.5)), float(value.get("y", 0.5))

    def angle(rect):
        value = rects[rect].get("m_LocalRotation") or {}
        return 2 * math.atan2(float(value.get("z", 0)), float(value.get("w", 1)))

    def local_matrix(rect):
        x, y = pos(rect)
        sx, sy = local_scale(rect)
        theta = angle(rect)
        c = math.cos(theta)
        s = math.sin(theta)
        return [[c * sx, -s * sy, x], [s * sx, c * sy, y], [0, 0, 1]]

    def chain_matrix(rect, stop_rect):
        chain = []
        current = rect
        while current and current != stop_rect:
            chain.append(current)
            current = parent(current)
        if current != stop_rect:
            return None
        matrix = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        for item in reversed(chain):
            matrix = mat_mul(matrix, local_matrix(item))
        return matrix

    def bbox(rect, stop_rect):
        matrix = chain_matrix(rect, stop_rect)
        if matrix is None:
            return None
        width, height = size(rect)
        px, py = pivot(rect)
        corners = [
            (-px * width, -py * height),
            ((1 - px) * width, -py * height),
            ((1 - px) * width, (1 - py) * height),
            (-px * width, (1 - py) * height),
        ]
        points = [transform(matrix, x, y) for x, y in corners]
        xs = [x for x, _ in points]
        ys = [y for _, y in points]
        return {
            "x": round(min(xs), 1),
            "y": round(min(ys), 1),
            "width": round(max(xs) - min(xs), 1),
            "height": round(max(ys) - min(ys), 1),
        }

    def ancestor_names(rect):
        result = []
        current = rect
        while current:
            result.append(go_name(go_of_rect(current)))
            current = parent(current)
        return result

    return comp_go, go_name, rect_of_go, bbox, ancestor_names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle",
        type=Path,
        default=ROOT / "local_device_cache" / "bd2_current_20260624" / "common-char-datingillust_assets_all.bundle",
    )
    parser.add_argument(
        "--only-advancing",
        action="store_true",
        help="只导出 IsNextStateWhenActionEnd=1 的阶段推进热区；默认导出全部互动点",
    )
    parser.add_argument(
        "--dating-id",
        help="只输出指定角色，例如 illust_dating1",
    )
    args = parser.parse_args()

    game_objects, components, rects, monos = load_bundle(args.bundle)
    comp_go, go_name, rect_of_go, bbox, ancestor_names = build_helpers(game_objects, components, rects)

    skeleton_rects = {}
    for go, data in game_objects.items():
        name = data.get("m_Name") or ""
        match = re.fullmatch(r"SkeletonGraphic \(illust_dating(\d+)\)", name)
        if match:
            skeleton_rects[f"illust_dating{match.group(1)}"] = rect_of_go(go)

    output = {}
    for mid, data in monos.items():
        if not all(
            key in data
            for key in ["_spineInteractionGroupId", "_spineInteractionId", "_interactionZoneShape"]
        ):
            continue
        if args.only_advancing and not data.get("IsNextStateWhenActionEnd"):
            continue

        rect = refid(data.get("_interactionBoxZoneRectTransform")) or refid(data.get("_rectTransform"))
        if not rect or rect not in rects:
            continue
        names = ancestor_names(rect)
        dating_id = next(
            (
                f"illust_dating{match.group(1)}"
                for name in names
                if name and (match := re.fullmatch(r"Illust_dating(\d+)", name))
            ),
            None,
        )
        if not dating_id or dating_id not in skeleton_rects:
            continue

        box = bbox(rect, skeleton_rects[dating_id])
        if not box:
            continue
        key = (
            f"{int(data['_spineInteractionGroupId'])}_"
            f"{int(data['_spineInteractionId'])}_"
            f"{int(data.get('spineInteractionToolId') or 0)}"
        )
        box.update(
            {
                "shape": int(data.get("_interactionZoneShape") or 0),
                "source": go_name(comp_go.get(rect)) or "RectTransform",
                "space": "skeleton",
            }
        )
        if args.dating_id and dating_id != args.dating_id:
            continue
        existing = output.setdefault(dating_id, {}).get(key)
        if existing is None or "[Override]" in (go_name(comp_go.get(rect)) or ""):
            output[dating_id][key] = box

    output = {
        dating_id: {key: items[key] for key in sorted(items, key=lambda value: tuple(map(int, value.split("_"))))}
        for dating_id, items in sorted(output.items())
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
