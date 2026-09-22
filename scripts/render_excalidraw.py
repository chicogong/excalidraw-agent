from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def abort(message: str) -> None:
    raise SystemExit(f"error: {message}")


def read_scene(path: Path) -> dict[str, Any]:
    if not path.is_file():
        abort(f"input does not exist: {path}")

    try:
        scene = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        abort(f"invalid JSON in {path}: {error}")

    if not isinstance(scene, dict) or scene.get("type") != "excalidraw":
        abort("the document must be an Excalidraw scene")
    if not isinstance(scene.get("elements"), list) or not scene["elements"]:
        abort("the scene must contain at least one element")
    if any(not isinstance(element, dict) for element in scene["elements"]):
        abort("every scene element must be an object")
    if "files" in scene and not isinstance(scene["files"], dict):
        abort("the top-level files field must be an object")
    return scene


def export_scene(
    source: Path,
    destination: Path,
    output_format: str,
    scale: int,
    max_dimension: int,
) -> None:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError:
        abort("Playwright is missing; run 'uv sync --project <skill>/scripts'")

    scene = read_scene(source)
    renderer = Path(__file__).with_name("renderer.html")
    if not renderer.is_file():
        abort(f"renderer page is missing: {renderer}")

    destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": 1280, "height": 720},
                device_scale_factor=scale,
            )
            page.goto(renderer.as_uri())
            page.wait_for_function("window.rendererReady === true", timeout=120_000)

            startup_error = page.evaluate("window.rendererError || null")
            if startup_error:
                abort(str(startup_error))

            result = page.evaluate(
                "async ([scene, limit]) => window.exportScene(scene, limit)",
                [scene, max_dimension],
            )
            if not isinstance(result, dict) or not result.get("ok"):
                abort(str(result.get("error", "renderer returned no result")))

            width = max(800, int(result["width"]) + 32)
            height = max(600, int(result["height"]) + 32)
            page.set_viewport_size({"width": width, "height": height})

            drawing = page.locator("#drawing > svg")
            if output_format == "svg":
                markup = drawing.evaluate(
                    "node => new XMLSerializer().serializeToString(node)"
                )
                destination.write_text(
                    '<?xml version="1.0" encoding="UTF-8"?>\n' + markup + "\n",
                    encoding="utf-8",
                )
            else:
                drawing.screenshot(path=str(destination), animations="disabled")
            browser.close()
    except PlaywrightError as error:
        abort(f"browser export failed: {error}")


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return number


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export an Excalidraw scene to PNG or SVG")
    parser.add_argument("input", type=Path, help="input .excalidraw file")
    parser.add_argument("--output", "-o", type=Path, help="output .png or .svg path")
    parser.add_argument(
        "--format",
        choices=("png", "svg"),
        help="output format; inferred from --output, otherwise PNG",
    )
    parser.add_argument("--scale", type=positive_int, default=2, help="PNG pixel density (default: 2)")
    parser.add_argument(
        "--max-dimension",
        type=positive_int,
        default=6000,
        help="maximum CSS width or height before raster scaling (default: 6000)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_format = args.format
    if output_format is None and args.output is not None:
        output_format = args.output.suffix.lower().lstrip(".")
    if output_format not in {"png", "svg"}:
        output_format = "png"

    output = args.output or args.input.with_suffix(f".{output_format}")
    if output.suffix.lower() != f".{output_format}":
        abort(f"output extension must be .{output_format}")

    export_scene(
        args.input.resolve(),
        output.resolve(),
        output_format,
        args.scale,
        args.max_dimension,
    )
    print(output.resolve())


if __name__ == "__main__":
    main()
