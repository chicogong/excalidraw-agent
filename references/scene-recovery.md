# Recovering an interactive Excalidraw scene

Use this procedure only when the user wants a local artifact to match a canvas edited in an interactive tool.

## Choose the strongest source

Use the first available source:

1. The tool's scene export or scene-read API.
2. A local file written by the tool.
3. The original scene payload plus explicit edit results.
4. A screenshot, as a visual reference only.

A screenshot cannot recover IDs, bindings, grouping, or editability. If it is the only source, describe the result as a recreation.

## Preserve scene semantics

For each element, preserve fields that affect layout or appearance, including:

- `id`, `type`, `x`, `y`, `width`, `height`, and `angle`
- stroke, fill, opacity, roughness, and roundness
- font family, font size, line height, text alignment, and original text
- arrow points, start/end bindings, and bound label relationships
- group, frame, link, and embedded-file references

Retain the scene's `appState.viewBackgroundColor` and top-level `files` object.

## Verify the recovery

1. Render the reconstructed `.excalidraw` file.
2. Compare the PNG with the interactive canvas at the same zoom or crop.
3. Correct layout differences in the source scene rather than editing the PNG.
4. Render twice with identical options and compare SHA-256 hashes.
5. Record only generic lessons in the reusable skill; keep private payloads and checkpoint values with the user's artifact.
