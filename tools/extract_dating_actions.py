#!/usr/bin/env python3
"""从心契 prefab 导出网页可用的互动 action 数据。

输出结构与 `dating.html` 中 `PREFAB_POINT_ACTIONS` 兼容。它不负责热区坐标；
坐标由 `extract_dating_hotzones.py` 生成。两者用同一个 key：
`<groupId>_<interactionId>_<toolId>`。
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


def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def transform(m, x, y):
    return m[0][0] * x + m[0][1] * y + m[0][2], m[1][0] * x + m[1][1] * y + m[1][2]


def vector_xy(value, default_x=0.0, default_y=0.0):
    value = value or {}
    return float(value.get("x", default_x)), float(value.get("y", default_y))


def build_rect_helpers(game_objects, components, rects, monos):
    comp_go = {component: go for go, items in components.items() for component in items}

    def go_name(go):
        return game_objects.get(go, {}).get("m_Name") or ""

    def rect_of_go(go):
        for component in components.get(go, []):
            if component in rects:
                return component
        return None

    def go_of_rect(rect):
        return comp_go.get(rect)

    def parent(rect):
        return refid(rects[rect].get("m_Father"))

    def local_scale(rect):
        return vector_xy(rects[rect].get("m_LocalScale"), 1.0, 1.0)

    def local_position(rect):
        return vector_xy(rects[rect].get("m_AnchoredPosition"))

    def size(rect):
        return vector_xy(rects[rect].get("m_SizeDelta"))

    def pivot(rect):
        return vector_xy(rects[rect].get("m_Pivot"), 0.5, 0.5)

    def angle(rect):
        value = rects[rect].get("m_LocalRotation") or {}
        return 2 * math.atan2(float(value.get("z", 0)), float(value.get("w", 1)))

    def local_matrix(rect):
        x, y = local_position(rect)
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

    def destination_rect(destination_path_id):
        destination = monos.get(destination_path_id) or {}
        go = refid(destination.get("m_GameObject"))
        return rect_of_go(go)

    skeleton_rects = {}
    for go, data in game_objects.items():
        name = data.get("m_Name") or ""
        match = re.fullmatch(r"SkeletonGraphic \(illust_dating(\d+)\)", name)
        if match:
            skeleton_rects[f"illust_dating{match.group(1)}"] = rect_of_go(go)

    return comp_go, go_name, parent, bbox, ancestor_names, destination_rect, skeleton_rects


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle",
        type=Path,
        default=ROOT / "local_device_cache" / "bd2_current_20260624" / "common-char-datingillust_assets_all.bundle",
    )
    parser.add_argument("--dating-id", help="只输出指定角色，例如 illust_dating1")
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="排除指定 dating-id；可重复。用于保留莎拉等手写特殊逻辑。",
    )
    args = parser.parse_args()

    game_objects, components, rects, monos = load_bundle(args.bundle)
    comp_go, go_name, parent, bbox, ancestor_names, destination_rect, skeleton_rects = build_rect_helpers(
        game_objects,
        components,
        rects,
        monos,
    )

    def go_of_rect(rect):
        return comp_go.get(rect)

    def list_value(value):
        return [item for item in (value or []) if item]

    def action_kind(value):
        return {0: "touch", 1: "drag", 2: "gyro"}.get(int(value or 0), "touch")

    def destination_refs(data):
        result = []
        for item in data.get("_destinations") or []:
            destination = refid(item)
            if destination and destination not in result:
                result.append(destination)
        single = refid(data.get("_interactionPointDestination"))
        if single and single not in result:
            result.append(single)
        return result

    def destination_boxes(dating_id, data):
        skeleton_rect = skeleton_rects.get(dating_id)
        if not skeleton_rect:
            return []
        result = []
        for idx, destination in enumerate(destination_refs(data)):
            rect = destination_rect(destination)
            if not rect:
                continue
            box = bbox(rect, skeleton_rect)
            if not box:
                continue
            names = ancestor_names(rect)
            box.update(
                {
                    "index": idx,
                    "source": names[0] or "InteractionPointDestination",
                    "space": "skeleton",
                }
            )
            result.append(box)
        return result

    output = {}
    for mid, data in monos.items():
        if not all(
            key in data
            for key in ["_spineInteractionGroupId", "_spineInteractionId", "_interactionActionType"]
        ):
            continue
        rect = refid(data.get("_rectTransform"))
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
        if not dating_id:
            continue
        if args.dating_id and dating_id != args.dating_id:
            continue
        if dating_id in args.exclude:
            continue

        group_id = int(data["_spineInteractionGroupId"])
        point_id = int(data["_spineInteractionId"])
        tool_id = int(data.get("spineInteractionToolId") or 0)
        key = f"{group_id}_{point_id}_{tool_id}"
        name = go_name(comp_go.get(mid))

        motions = list_value(data.get("_playMotionNames"))
        play_motion = data.get("PlayMotionName")
        if play_motion and play_motion not in motions:
            motions.append(play_motion)

        action = {
            "kind": action_kind(data.get("_interactionActionType")),
            "mix": list_value(data.get("PlayMixAnimNames")),
        }
        if motions:
            action["motions"] = motions
        if data.get("IsNextStateWhenActionEnd"):
            forced = int(data.get("ForceIdleWhenNextState") or 0)
            action["nextStage"] = forced if forced else "next"
        click_max = int(data.get("ClickMaxCount") or 0)
        if click_max:
            action["clickMax"] = click_max
            reset = float(data.get("ContinuousClickResetTime") or 0)
            if reset:
                action["clickReset"] = reset
        if data.get("IsPlayRandomMixAnim"):
            action["randomMix"] = True
        stop_mix = data.get("PlayMixAnimNameWhenActionStop") or ""
        if stop_mix:
            action["stopMix"] = stop_mix
        destinations = destination_boxes(dating_id, data)
        if destinations:
            action["destinations"] = destinations
        if "hidden" in name.lower():
            action["hidden"] = True

        gauge = data.get("_gaugeSettingData") or {}
        if gauge.get("IsOn"):
            action["gauge"] = True

        long_press = data.get("_longPressSettingData") or {}
        if long_press.get("ActionType"):
            action["longPress"] = {
                "actionType": int(long_press.get("ActionType") or 0),
                "threshold": float(long_press.get("ThresholdTime") or 0),
                "loop": long_press.get("LoopMixAnimationName") or "",
                "fail": long_press.get("FailMixAnimationName") or "",
                "success": long_press.get("SuccessMixAnimationName") or "",
            }

        gyro = data.get("_gyroSettingData") or {}
        if gyro.get("_actionType"):
            action["gyro"] = {
                "actionType": int(gyro.get("_actionType") or 0),
                "moveThreshold": float(gyro.get("_movePointThreshold") or 0),
                "moveSensitivity": float(gyro.get("_movePointSensitivity") or 0),
                "shakingThreshold": float(gyro.get("_shakingThreshold") or 0),
                "shakingHoldTime": float(gyro.get("_shakingHoldTime") or 0),
            }

        existing = output.setdefault(dating_id, {}).get(key)
        if existing is None or "[Override]" in name:
            output[dating_id][key] = action

    output = {
        dating_id: {key: items[key] for key in sorted(items, key=lambda value: tuple(map(int, value.split("_"))))}
        for dating_id, items in sorted(output.items())
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
