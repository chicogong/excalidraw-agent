---
name: excalidraw-agent
description: Create or revise editable Excalidraw diagrams, show them through the Excalidraw MCP interactive canvas, and verify local PNG or SVG exports. Use for architecture, workflow, sequence, relationship, and explanatory diagrams when the user needs an interactive view, an .excalidraw source, a rendered preview, or recovery of an edited canvas.
---

# Excalidraw Agent

Combine the Excalidraw MCP experience with reproducible local artifacts. The MCP canvas is the interactive view; the local `.excalidraw` file is the durable source; the PNG/SVG renderer verifies that source.

## Workflow

1. Identify the statement the diagram should make and choose a structure that expresses it: sequence, hierarchy, fan-out, convergence, comparison, or feedback loop.
2. Use real names and evidence for technical diagrams. Do not replace known APIs, events, payloads, or components with generic placeholders.
3. When the Excalidraw MCP tools are available, call `read_me` once, then use `create_view` to show and iterate on the diagram. Follow the live tool schema because it may be newer than this skill.
4. When a durable artifact is requested, maintain a native `.excalidraw` scene as the canonical copy. Use `scripts/prepare_mcp_payload.py` to send that scene to `create_view` without changing the local source.
5. Render the canonical scene with `scripts/render_excalidraw.py` and inspect a PNG preview. Fix clipping, overlaps, weak hierarchy, crossed arrows, and excessive empty space before delivery. Export SVG when the user needs a vector artifact.
6. Deliver the requested interactive view and, when applicable, both the editable source and verified preview.

## Choose the State Model

- **Interactive-only:** MCP checkpoints may be the working state. Use `restoreCheckpoint` for later turns.
- **Reproducible deliverable:** the local `.excalidraw` file is canonical. Mirror agent-authored changes into it before rendering.
- **User edited in fullscreen:** the checkpoint contains those edits, but the model-facing tools do not expose the full scene. Do not claim the local file matches until the user exports/downloads the edited scene or a scene-read tool becomes available.

Read [references/mcp-workflow.md](references/mcp-workflow.md) before combining MCP interaction with local export.

## MCP Preview

Prepare the initial `create_view` payload from a local scene:

```bash
python {baseDir}/scripts/prepare_mcp_payload.py \
  /absolute/path/diagram.excalidraw \
  --output /tmp/diagram.mcp.json
```

Pass the resulting JSON array as the `elements` argument to `create_view`. The script deliberately rejects MCP shorthand labels and embedded files because those cannot round-trip through the current local renderer without changing semantics.

For iterative MCP-only edits, retain the returned checkpoint ID and send only:

```json
[
  {"type":"restoreCheckpoint","id":"<checkpoint-id>"},
  {"type":"delete","ids":"old-id"},
  {"type":"rectangle","id":"replacement-id","x":100,"y":100,"width":200,"height":80}
]
```

Checkpoint IDs are runtime state. Do not write them into the reusable skill or publish them.

## Render

Set up the renderer once:

```bash
uv sync --project {baseDir}/scripts
uv run --project {baseDir}/scripts playwright install chromium
```

Render PNG and SVG files:

```bash
uv run --project {baseDir}/scripts python {baseDir}/scripts/render_excalidraw.py \
  /absolute/path/diagram.excalidraw \
  --output /absolute/path/diagram.png

uv run --project {baseDir}/scripts python {baseDir}/scripts/render_excalidraw.py \
  /absolute/path/diagram.excalidraw \
  --output /absolute/path/diagram.svg
```

The browser downloads a pinned `@excalidraw/utils` module from jsDelivr at render time. Report a network dependency failure instead of silently substituting a different renderer.

## Interactive Canvas Recovery

An interactive canvas checkpoint is not automatically a local `.excalidraw` file.

- Prefer a model-visible scene read/export operation when available. The current official MCP exposes `read_me` and `create_view` to the model; checkpoint read/save and upload are app-private.
- If only scene creation and checkpoint IDs are available, retain the original scene payload and agent-authored changes. Treat fullscreen user edits as checkpoint-only until the edited scene is exported by the user.
- Preserve element IDs, coordinates, dimensions, colors, font families, bindings, and label wrapping when fidelity matters.
- Render twice and compare hashes before claiming that a recovered export is stable.

Read [references/scene-recovery.md](references/scene-recovery.md) when recovering a canvas rather than creating a new diagram.

## Boundaries

- Do not call a redraw an export. Say when a scene was reconstructed.
- Do not publish local session logs, checkpoints, private diagrams, or machine-specific paths.
- Keep diagram-specific recovery scripts beside the diagram, not inside this reusable skill.
- If the source scene contains embedded files, preserve its top-level `files` object.
