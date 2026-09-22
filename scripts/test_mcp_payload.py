from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
PREPARE = HERE / "prepare_mcp_payload.py"


def scene(elements: list[dict], files: dict | None = None) -> dict:
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"viewBackgroundColor": "#ffffff"},
        "files": files or {},
    }


def rectangle(element_id: str = "box") -> dict:
    return {
        "id": element_id,
        "type": "rectangle",
        "x": 100,
        "y": 100,
        "width": 200,
        "height": 80,
        "isDeleted": False,
    }


def run(input_path: Path, output_path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PREPARE), str(input_path), "--output", str(output_path)],
        text=True,
        capture_output=True,
    )


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="excalidraw-mcp-payload-test-") as directory:
        root = Path(directory)
        input_path = root / "scene.excalidraw"
        output_path = root / "payload.json"

        input_path.write_text(json.dumps(scene([rectangle()])), encoding="utf-8")
        result = run(input_path, output_path)
        if result.returncode != 0:
            raise SystemExit(result.stderr)

        payload = json.loads(output_path.read_text(encoding="utf-8"))
        if payload[0].get("type") != "cameraUpdate":
            raise SystemExit("payload does not start with cameraUpdate")
        if (payload[0]["width"], payload[0]["height"]) not in {
            (400, 300),
            (600, 450),
            (800, 600),
            (1200, 900),
            (1600, 1200),
        }:
            raise SystemExit("payload uses a non-standard camera size")
        if payload[1]["id"] != "box":
            raise SystemExit("native element order was not preserved")

        labeled = rectangle("labeled")
        labeled["label"] = {"text": "not native"}
        input_path.write_text(json.dumps(scene([labeled])), encoding="utf-8")
        result = run(input_path, output_path)
        if result.returncode == 0 or "label shorthand" not in result.stderr:
            raise SystemExit("MCP label shorthand was not rejected")

        input_path.write_text(
            json.dumps(scene([rectangle()], {"image": {"dataURL": "data:image/png;base64,AA=="}})),
            encoding="utf-8",
        )
        result = run(input_path, output_path)
        if result.returncode == 0 or "embedded files" not in result.stderr:
            raise SystemExit("embedded files were not rejected")

        print("ok: native scene converts to a bounded MCP payload")


if __name__ == "__main__":
    main()
