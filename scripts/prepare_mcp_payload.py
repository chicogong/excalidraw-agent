from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any


MAX_PAYLOAD_BYTES = 5 * 1024 * 1024
CAMERA_SIZES = ((400, 300), (600, 450), (800, 600), (1200, 900), (1600, 1200))
PSEUDO_TYPES = {"cameraUpdate", "restoreCheckpoint", "delete"}


def abort(message: str) -> None:
    raise SystemExit(f"error: {message}")


def read_scene(path: Path) -> dict[str, Any]:
    try:
        scene = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        abort(f"input does not exist: {path}")
    except json.JSONDecodeError as error:
        abort(f"invalid JSON in {path}: {error}")

    if not isinstance(scene, dict) or scene.get("type") != "excalidraw":
        abort("the input must be a native Excalidraw document")
    if not isinstance(scene.get("elements"), list) or not scene["elements"]:
        abort("the scene must contain at least one element")
    if scene.get("files"):
        abort("embedded files are not supported by the elements-only MCP input")
    return scene


def element_bounds(element: dict[str, Any]) -> tuple[float, float, float, float]:
    x = float(element.get("x", 0))
    y = float(element.get("y", 0))
    width = abs(float(element.get("width", 0)))
    height = abs(float(element.get("height", 0)))

    points = element.get("points")
    if element.get("type") in {"arrow", "line"} and isinstance(points, list) and points:
        xs = [x + float(point[0]) for point in points]
        ys = [y + float(point[1]) for point in points]
        return min(xs), min(ys), max(xs), max(ys)
    return x, y, x + width, y + height


def validate_elements(elements: list[Any]) -> list[dict[str, Any]]:
    active: list[dict[str, Any]] = []
    ids: set[str] = set()

    for index, element in enumerate(elements):
        if not isinstance(element, dict):
            abort(f"element {index} is not an object")
        if element.get("isDeleted"):
            continue
        if element.get("type") in PSEUDO_TYPES:
            abort(f"element {index} contains MCP-only type {element.get('type')!r}")
        if "label" in element:
            abort(
                f"element {index} uses MCP label shorthand; use native bound text for local/MCP parity"
            )

        element_id = element.get("id")
        if not isinstance(element_id, str) or not element_id:
            abort(f"element {index} has no string id")
        if element_id in ids:
            abort(f"duplicate element id: {element_id}")
        ids.add(element_id)
        active.append(element)

    if not active:
        abort("the scene contains no active elements")
    return active


def estimated_text_width(value: str, font_size: float) -> float:
    """Estimate Excalifont's line width for MCP's left-anchored text input."""
    widths = []
    for line in value.split("\n"):
        units = 0.0
        for character in line:
            if unicodedata.east_asian_width(character) in {"W", "F"}:
                units += 1.0
            elif character in " iljtfr.,:;!|\u2019'`":
                units += 0.34
            elif character in "MW@#%&":
                units += 0.8
            else:
                units += 0.55
        widths.append(units * font_size)
    return max(widths, default=0.0)


def adapt_text_for_mcp(element: dict[str, Any]) -> dict[str, Any]:
    """Keep native text positioning out of MCP's shorthand alignment rules."""
    if element.get("type") != "text" or element.get("containerId"):
        return element
    alignment = element.get("textAlign", "left")
    if alignment not in {"center", "right"}:
        return element

    width = float(element.get("width", 0))
    if width <= 0:
        return element
    text_width = estimated_text_width(str(element.get("text", "")), float(element.get("fontSize", 20)))
    x = float(element.get("x", 0))
    if alignment == "center":
        x += (width - text_width) / 2
    else:
        x += width - text_width

    adapted = dict(element)
    adapted["x"] = round(x, 2)
    adapted["textAlign"] = "left"
    return adapted


def automatic_camera(elements: list[dict[str, Any]], padding: int) -> dict[str, Any]:
    bounds = [element_bounds(element) for element in elements]
    min_x = min(bound[0] for bound in bounds) - padding
    min_y = min(bound[1] for bound in bounds) - padding
    content_width = max(bound[2] for bound in bounds) - min_x + padding
    content_height = max(bound[3] for bound in bounds) - min_y + padding

    width, height = CAMERA_SIZES[-1]
    for candidate_width, candidate_height in CAMERA_SIZES:
        if content_width <= candidate_width and content_height <= candidate_height:
            width, height = candidate_width, candidate_height
            break
    else:
        print(
            "warning: content exceeds the largest 1600x1200 MCP camera and may be cropped",
            file=sys.stderr,
        )

    center_x = min_x + content_width / 2
    center_y = min_y + content_height / 2
    return {
        "type": "cameraUpdate",
        "x": round(center_x - width / 2),
        "y": round(center_y - height / 2),
        "width": width,
        "height": height,
    }


def build_payload(scene: dict[str, Any], padding: int) -> list[dict[str, Any]]:
    elements = validate_elements(scene["elements"])
    adapted = [adapt_text_for_mcp(element) for element in elements]
    return [automatic_camera(adapted, padding), *adapted]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a native .excalidraw document to an Excalidraw MCP create_view payload"
    )
    parser.add_argument("input", type=Path, help="native .excalidraw document")
    parser.add_argument("--output", "-o", type=Path, help="output JSON array; defaults to stdout")
    parser.add_argument("--padding", type=int, default=60, help="camera padding in scene pixels")
    parser.add_argument("--pretty", action="store_true", help="indent the output for inspection")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.padding < 0:
        abort("padding must not be negative")

    payload = build_payload(read_scene(args.input.resolve()), args.padding)
    text = json.dumps(
        payload,
        ensure_ascii=False,
        indent=2 if args.pretty else None,
        separators=None if args.pretty else (",", ":"),
    )
    if len(text.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        abort("payload exceeds the current MCP 5 MiB input limit")

    if args.output:
        args.output.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.output.resolve().write_text(text + "\n", encoding="utf-8")
        print(args.output.resolve())
    else:
        print(text)


if __name__ == "__main__":
    main()
