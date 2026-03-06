# API Testing with VS Code REST Client

This folder contains a ready-to-run REST Client collection for ReformLab:

- `reformlab-api.http`

## Quick start

1. Start backend server:
   - VS Code task: `Backend: API Server`
   - This task sets `REFORMLAB_PASSWORD=local`
2. Open `reformlab-api.http`.
3. Switch environment:
   - Command Palette -> `Rest Client: Switch Environment` -> `local`
4. Click `Send Request` on `Login`, then run requests top-to-bottom.

## One-command smoke workflow

You can also run a full API smoke flow directly from VS Code tasks:

- `API: Quick Workflow Smoke Test` (expects backend already running)
- `API: Start Backend + Smoke Test` (one-shot: starts temp backend on `:8011`, runs smoke test, then stops it)

Smoke implementation file: `examples/api/api_smoke_test.py`

If simulation data is not configured locally, the smoke script automatically
falls back to a "degraded mode" that still validates auth, template discovery,
memory check, and error contracts for indicators/comparison/exports.

## How variable chaining works

- `# @name login` names a request.
- Later requests read values from it:
  - `{{login.response.body.$.token}}` -> bearer token
- Same idea for run IDs:
  - `{{runBaseline.response.body.$.run_id}}`

This lets you execute full flows (login -> run -> indicators -> export) without copy/paste.
