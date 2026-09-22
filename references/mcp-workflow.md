# Excalidraw MCP workflow

Use this reference when the task needs both an inline interactive canvas and files that can be committed or embedded elsewhere.

## Current capability boundary

The official Excalidraw MCP exposes two model-facing tools:

- `read_me`: returns the current element schema, palette, camera rules, and examples.
- `create_view`: streams elements into an interactive widget and returns a checkpoint ID.

The widget also uses app-private tools for checkpoint read/save and upload to excalidraw.com. Those private tools are not a model-facing file export API.

`create_view` supports MCP-only pseudo-elements:

- `cameraUpdate`: changes the animated viewport.
- `restoreCheckpoint`: loads an earlier checkpoint before applying new elements.
- `delete`: removes IDs from the restored state.

Do not persist these pseudo-elements inside a native `.excalidraw` document.

## Local-first flow

Use this flow when the user needs files or repeatable export:

1. Create or update a native `.excalidraw` document locally.
2. Avoid the MCP `label` shorthand; represent labels as native text/binding elements so the MCP view and local renderer share the same scene semantics.
3. Run `prepare_mcp_payload.py` to prepend a camera and produce the JSON array expected by `create_view`.
4. Show the interactive MCP view and retain its returned checkpoint only for this task.
5. Apply agent-authored changes to the local source as well as the checkpoint.
6. Render the local source and visually inspect the PNG.

If the user edits the fullscreen canvas, the checkpoint is newer than the local file. Ask the user to use the widget's export action and provide the resulting scene before claiming exact local parity.

## MCP-first flow

Use this flow when the user mainly wants to explore or iterate in chat:

1. Call `read_me` once per conversation.
2. Start `create_view` with a `cameraUpdate` followed by elements in visual draw order.
3. For later edits, begin with `restoreCheckpoint`, then add `delete` and replacement/new elements.
4. Treat the checkpoint as ephemeral runtime state, not a repository artifact.
5. If the user later requests local files, recover from an exported scene when possible. Otherwise disclose that the local result is a reconstruction.

## Fidelity limits

- Screenshot feedback is useful for visual review but cannot recover element IDs, bindings, or full styling.
- The widget's edit context reports a compact change summary; it is not a complete scene serialization.
- Embedded image/file payloads do not fit the elements-only `create_view` input and require a separate supported transfer path.
- Checkpoints may expire or be unavailable after service/session changes. Keep durable work in a local source file.
