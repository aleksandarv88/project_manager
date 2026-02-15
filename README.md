# project_manager

## Project Summary
Internal VFX pipeline WIP platform with a Django web app, REST-style API endpoints, and Houdini-facing Python tooling.  
It tracks projects/assets/tasks/shots and records scene/publish events into PostgreSQL.  
The goal is to provide deterministic save/publish behavior and a single DB-backed source for desktop UI and DCC integrations.

## What Works Now
- Django app runs locally on `127.0.0.1:8002` with PostgreSQL backend.
- CRUD-style API endpoints exist for projects, assets, sequences, shots, artists, tasks, scenes, and publishes.
- Publish API supports part-style publishes with `item_usd_path` + `asset_usd_path` and source version/iteration fields.
- Scene save flow supports version/iteration numbering and records results in DB/API.
- Desktop PySide artist manager launches DCC sessions with pipeline context env vars.
- A dev-only DB data reset command exists: `python manage.py dev_reset_db --yes`.
- Publish query mode supports latest unique parts per asset via `latest_per_part=1`.

## What Is WIP
- Shared USD layer orchestration is functional but still evolving for production robustness.
- Validation/normalization around asset/part metadata is currently pragmatic, not fully strict.
- Test coverage is minimal; most validation is manual/integration-oriented.
- Houdini-side UX and shelf tooling are still iterative.
- Deployment/security hardening (production settings, secrets management) is not finalized.

## Tech Stack
- Python 3.10+
- Django 5.x
- PostgreSQL + psycopg2
- PySide2 desktop UI
- Houdini/Maya integration scripts (optional for local web/API demo)

## Quickstart
1. Clone and enter repo.
```bash
git clone <your-repo-url>
cd project_manager
```

2. Create and activate a virtual environment.
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

3. Install dependencies.
```bash
pip install -r requirements.txt
```

4. Create env file from example and edit values.
```bash
copy .env.example .env
```

5. Export environment variables (or load from `.env` in your shell/session).
```bash
# Windows PowerShell example
$env:PM_DB_NAME="FX3X"
$env:PM_DB_USER="postgres"
$env:PM_DB_PASSWORD="<your_password>"
$env:PM_DB_HOST="localhost"
$env:PM_DB_PORT="5432"
$env:DJANGO_SECRET_KEY="<your_secret_key>"
$env:DJANGO_DEBUG="1"
```

6. Run migrations and start Django.
```bash
cd django_pipeline/vfx_pipeline
python manage.py migrate
python manage.py runserver 127.0.0.1:8002
```

7. Optional dev data reset (keeps schema/migrations).
```bash
python manage.py dev_reset_db --yes
```

## API Demo
Example publish request:
```bash
curl -X POST "http://127.0.0.1:8002/api/publishes/" ^
  -H "Content-Type: application/json" ^
  -d "{\"task_id\":32,\"target_type\":\"shot\",\"target_id\":11,\"software\":\"houdini\",\"source_version\":1,\"source_iteration\":1,\"item_usd_path\":\"/show/sequences/010/0500/fx/houdini/scenes/artist01/PinchIn/usd/PinchIn/particles01/data/particles01_v001_i001.usd\",\"asset_usd_path\":\"/show/sequences/010/0500/fx/houdini/scenes/artist01/PinchIn/usd/PinchIn/particles01/particles01.usd\",\"status\":\"published\",\"metadata\":{\"asset_name\":\"PinchIn\",\"part_name\":\"particles01\"}}"
```

Example response:
```json
{
  "ok": true,
  "data": {
    "publish_id": 21,
    "id": 21,
    "source_version": 1,
    "source_iteration": 1,
    "version": 1,
    "iteration": 1,
    "is_latest": true,
    "part_name": "particles01",
    "part_usd_path": "/show/sequences/010/0500/fx/houdini/scenes/artist01/PinchIn/usd/PinchIn/particles01/particles01.usd"
  }
}
```

Latest unique parts for an asset:
```bash
curl "http://127.0.0.1:8002/api/publishes/?asset=PinchIn&latest_per_part=1"
```

Run the built-in demo script (no Houdini required):
```bash
set API_BASE_URL=http://127.0.0.1:8002
set DEMO_TASK_ID=1
set DEMO_TARGET_ID=1
python tools/demo_api_publish.py
```

## Notes For Houdini Integration
- Houdini is not required to run/review the Django app or API demo flow.
- Houdini-facing helpers live under `pipeline_scripts/houdini/`.
- Typical publish env vars used by tools: `PM_API_URL`, `PM_API_TOKEN`, `PM_TASK_ID`, `PM_ARTIST`.
