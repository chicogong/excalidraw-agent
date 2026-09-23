"""Generate the two editable workflow figures used by the README."""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
INK = "#172033"
MUTED = "#536477"
BLUE = "#3578e5"
PURPLE = "#8056e8"
GREEN = "#2fa86a"
ORANGE = "#e88816"


class Diagram:
    def __init__(self) -> None:
        self.elements: list[dict] = []

    def base(self, element_id: str, kind: str, x: int, y: int, width: int, height: int) -> dict:
        return {
            "id": element_id,
            "type": kind,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "angle": 0,
            "strokeColor": INK,
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 0,
            "opacity": 100,
            "groupIds": [],
            "frameId": None,
            "index": f"a{len(self.elements):04d}",
            "roundness": None,
            "seed": 2000 + len(self.elements) * 37,
            "version": 1,
            "versionNonce": 7000 + len(self.elements) * 53,
            "isDeleted": False,
            "boundElements": [],
            "updated": 1,
            "link": None,
            "locked": False,
        }

    def box(self, element_id: str, x: int, y: int, width: int, height: int, stroke: str, fill: str, dashed: bool = False) -> None:
        element = self.base(element_id, "rectangle", x, y, width, height)
        element.update(
            strokeColor=stroke,
            backgroundColor=fill,
            strokeStyle="dashed" if dashed else "solid",
            roundness={"type": 3},
        )
        self.elements.append(element)

    def text(self, element_id: str, value: str, x: int, y: int, width: int, size: int, color: str = INK, align: str = "left") -> None:
        height = round(size * 1.3)
        element = self.base(element_id, "text", x, y, width, height)
        element.update(
            strokeColor=color,
            strokeWidth=1,
            text=value,
            fontSize=size,
            fontFamily=5,
            textAlign=align,
            verticalAlign="top",
            containerId=None,
            originalText=value,
            autoResize=False,
            lineHeight=1.25,
        )
        self.elements.append(element)

    def arrow(self, element_id: str, points: list[tuple[int, int]], color: str, dashed: bool = False) -> None:
        x, y = points[0]
        relative = [[px - x, py - y] for px, py in points]
        element = self.base(element_id, "arrow", x, y, points[-1][0] - x, points[-1][1] - y)
        element.update(
            strokeColor=color,
            strokeWidth=3,
            strokeStyle="dashed" if dashed else "solid",
            roundness={"type": 2},
            points=relative,
            lastCommittedPoint=None,
            startBinding=None,
            endBinding=None,
            startArrowhead=None,
            endArrowhead="arrow",
            elbowed=False,
        )
        self.elements.append(element)

    def save(self, filename: str) -> None:
        scene = {
            "type": "excalidraw",
            "version": 2,
            "source": "https://excalidraw.com",
            "elements": self.elements,
            "appState": {"viewBackgroundColor": "#ffffff"},
            "files": {},
        }
        (HERE / filename).write_text(json.dumps(scene, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def pipeline() -> None:
    d = Diagram()
    d.box("mcp-lane", 25, 275, 500, 315, "#cbd5e1", "#f8f6ff", dashed=True)
    d.box("export-lane", 555, 275, 500, 315, "#cbd5e1", "#f6fbff", dashed=True)
    d.arrow("source-to-mcp", [(450, 230), (275, 355)], PURPLE)
    d.arrow("source-to-export", [(630, 230), (805, 355)], BLUE)
    d.arrow("payload-to-view", [(275, 430), (275, 475)], PURPLE)
    d.arrow("renderer-to-files", [(805, 430), (805, 475)], BLUE)

    d.box("scene", 340, 140, 400, 90, BLUE, "#eaf3ff")
    d.box("payload", 60, 355, 430, 75, PURPLE, "#f0eaff")
    d.box("view", 60, 475, 430, 85, PURPLE, "#f0eaff")
    d.box("renderer", 590, 355, 430, 75, GREEN, "#e7f8ee")
    d.box("files", 590, 475, 430, 85, GREEN, "#e7f8ee")

    d.text("title", "One source, two paths", 35, 28, 1010, 38)
    d.text("subtitle", "Keep the editable scene local; preview with MCP or export files from that same scene.", 36, 82, 1000, 19, MUTED)
    d.text("scene-title", "diagram.excalidraw", 360, 157, 360, 26, align="center")
    d.text("scene-detail", "Canonical editable source", 360, 195, 360, 17, MUTED, align="center")
    d.text("mcp-lane-title", "Interactive MCP canvas", 50, 294, 445, 22, PURPLE)
    d.text("export-lane-title", "Local export", 580, 294, 445, 22, BLUE)
    d.text("payload-title", "prepare_mcp_payload.py", 80, 366, 390, 22, align="center")
    d.text("payload-detail", "Native elements → MCP array", 80, 397, 390, 16, MUTED, align="center")
    d.text("view-title", "create_view → canvas", 80, 489, 390, 22, align="center")
    d.text("view-detail", "Checkpoint stays in the MCP runtime", 80, 521, 390, 16, MUTED, align="center")
    d.text("renderer-title", "render_excalidraw.py", 610, 366, 390, 22, align="center")
    d.text("renderer-detail", "Reads the native scene directly", 610, 397, 390, 16, MUTED, align="center")
    d.text("files-title", "PNG preview + SVG export", 610, 489, 390, 22, align="center")
    d.text("files-detail", "Inspect the result before sharing", 610, 521, 390, 16, MUTED, align="center")
    d.text("note", "Fullscreen canvas edits need a scene export before the local file can match.", 45, 607, 990, 17, MUTED, align="center")
    d.save("mcp-local-export-pipeline.excalidraw")


def checkpoint() -> None:
    d = Diagram()
    d.box("runtime-lane", 25, 135, 1030, 245, "#cbd5e1", "#f8f6ff", dashed=True)
    d.box("local-lane", 25, 425, 1030, 185, "#cbd5e1", "#f5fbf7", dashed=True)
    d.arrow("initial-to-checkpoint", [(270, 267), (305, 267)], PURPLE)
    d.arrow("checkpoint-to-restore", [(530, 267), (565, 267)], PURPLE)
    d.arrow("restore-to-updated", [(790, 267), (825, 267)], PURPLE)
    d.arrow("mirror-to-source", [(405, 535), (455, 535)], GREEN)
    d.arrow("source-to-render", [(685, 535), (735, 535)], GREEN)
    d.arrow("mirror-agent-delta", [(675, 317), (675, 395), (292, 395), (292, 485)], ORANGE, dashed=True)

    d.box("initial", 45, 217, 225, 100, PURPLE, "#f0eaff")
    d.box("checkpoint-one", 305, 217, 225, 100, ORANGE, "#fff3df")
    d.box("restore-edit", 565, 217, 225, 100, PURPLE, "#f0eaff")
    d.box("updated", 825, 217, 225, 100, PURPLE, "#f0eaff")
    d.box("mirror", 180, 485, 225, 100, ORANGE, "#fff3df")
    d.box("scene", 455, 485, 230, 100, BLUE, "#eaf3ff")
    d.box("export", 735, 485, 225, 100, GREEN, "#e7f8ee")

    d.text("title", "Iterate with checkpoints", 35, 27, 1000, 38)
    d.text("subtitle", "The canvas remembers a session; the local scene preserves a deliverable.", 36, 82, 1000, 19, MUTED)
    d.text("runtime-label", "MCP runtime · temporary state", 50, 151, 950, 22, PURPLE)
    d.text("local-label", "Local source · durable state", 710, 440, 320, 22, GREEN)
    d.text("initial-title", "create_view", 62, 235, 190, 22, align="center")
    d.text("initial-detail", "Initial scene", 62, 273, 190, 16, MUTED, align="center")
    d.text("checkpoint-title", "checkpoint #1", 322, 235, 190, 22, align="center")
    d.text("checkpoint-detail", "Saved by MCP", 322, 273, 190, 16, MUTED, align="center")
    d.text("restore-title", "restore + edit", 582, 235, 190, 22, align="center")
    d.text("restore-detail", "delete + add elements", 582, 273, 190, 16, MUTED, align="center")
    d.text("updated-title", "updated canvas", 842, 235, 190, 22, align="center")
    d.text("updated-detail", "New checkpoint", 842, 273, 190, 16, MUTED, align="center")
    d.text("delta-label", "agent edits", 700, 380, 145, 15, ORANGE)
    d.text("mirror-title", "mirror edits", 197, 503, 190, 22, align="center")
    d.text("mirror-detail", "Agent-authored delta", 197, 541, 190, 16, MUTED, align="center")
    d.text("scene-title", "scene.excalidraw", 472, 503, 196, 22, align="center")
    d.text("scene-detail", "Canonical source", 472, 541, 196, 16, MUTED, align="center")
    d.text("export-title", "render PNG / SVG", 752, 503, 190, 22, align="center")
    d.text("export-detail", "Verified artifacts", 752, 541, 190, 16, MUTED, align="center")
    d.text("note", "For manual fullscreen edits, export the edited scene before claiming local parity.", 45, 628, 990, 17, MUTED, align="center")
    d.save("checkpoint-iteration.excalidraw")


if __name__ == "__main__":
    pipeline()
    checkpoint()
