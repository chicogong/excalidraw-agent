from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path


HERE = Path(__file__).resolve().parent
RENDERER = HERE / "render_excalidraw.py"


def text_element(element_id: str, text: str, x: int, y: int, width: int, font_family: int) -> dict:
    return {
        "id": element_id,
        "type": "text",
        "x": x,
        "y": y,
        "width": width,
        "height": 32,
        "angle": 0,
        "strokeColor": "#1e1e1e",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 1,
        "strokeStyle": "solid",
        "roughness": 0,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "index": "a0",
        "roundness": None,
        "seed": 1,
        "version": 1,
        "versionNonce": 1,
        "isDeleted": False,
        "boundElements": [],
        "updated": 1,
        "link": None,
        "locked": False,
        "text": text,
        "fontSize": 24,
        "fontFamily": font_family,
        "textAlign": "left",
        "verticalAlign": "top",
        "containerId": None,
        "originalText": text,
        "autoResize": False,
        "lineHeight": 1.25,
    }


def fixture() -> dict:
    title = text_element("title", "Excalidraw 导出测试", 80, 50, 360, 5)
    code = text_element("code", "LLM -> Tool Call -> Result", 120, 190, 420, 3)
    box = {
        "id": "box",
        "type": "rectangle",
        "x": 80,
        "y": 150,
        "width": 520,
        "height": 100,
        "angle": 0,
        "strokeColor": "#1971c2",
        "backgroundColor": "#d0ebff",
        "fillStyle": "solid",
        "strokeWidth": 2,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "index": "a1",
        "roundness": {"type": 3},
        "seed": 2,
        "version": 1,
        "versionNonce": 2,
        "isDeleted": False,
        "boundElements": [],
        "updated": 1,
        "link": None,
        "locked": False,
    }
    arrow = {
        "id": "arrow",
        "type": "arrow",
        "x": 340,
        "y": 260,
        "width": 0,
        "height": 100,
        "angle": 0,
        "strokeColor": "#1971c2",
        "backgroundColor": "transparent",
        "fillStyle": "solid",
        "strokeWidth": 3,
        "strokeStyle": "solid",
        "roughness": 1,
        "opacity": 100,
        "groupIds": [],
        "frameId": None,
        "index": "a2",
        "roundness": {"type": 2},
        "seed": 3,
        "version": 1,
        "versionNonce": 3,
        "isDeleted": False,
        "boundElements": [],
        "updated": 1,
        "link": None,
        "locked": False,
        "points": [[0, 0], [0, 100]],
        "lastCommittedPoint": None,
        "startBinding": None,
        "endBinding": None,
        "startArrowhead": None,
        "endArrowhead": "arrow",
        "elbowed": False,
    }
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": [title, box, code, arrow],
        "appState": {"viewBackgroundColor": "#ffffff"},
        "files": {},
    }


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="excalidraw-skill-test-") as directory:
        root = Path(directory)
        scene = root / "fixture.excalidraw"
        first = root / "first.png"
        second = root / "second.png"
        first_svg = root / "first.svg"
        second_svg = root / "second.svg"
        scene.write_text(json.dumps(fixture(), ensure_ascii=False), encoding="utf-8")

        for output in (first, second):
            subprocess.run(
                [sys.executable, str(RENDERER), str(scene), "--output", str(output)],
                check=True,
            )

        if not first.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            raise SystemExit("renderer did not create a PNG")
        if digest(first) != digest(second):
            raise SystemExit("repeated exports are not deterministic")

        for output in (first_svg, second_svg):
            subprocess.run(
                [sys.executable, str(RENDERER), str(scene), "--output", str(output)],
                check=True,
            )

        try:
            root_element = ET.parse(first_svg).getroot()
        except ET.ParseError as error:
            raise SystemExit(f"renderer did not create valid SVG: {error}")
        if not root_element.tag.endswith("svg"):
            raise SystemExit("renderer output root is not SVG")
        if digest(first_svg) != digest(second_svg):
            raise SystemExit("repeated SVG exports are not deterministic")

        print(f"ok: deterministic PNG {digest(first)}")
        print(f"ok: deterministic SVG {digest(first_svg)}")


if __name__ == "__main__":
    main()
