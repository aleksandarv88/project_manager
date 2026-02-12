# project_manager

Work-in-progress project manager / pipeline prototype.

## Structure
- `django_pipeline/` - Django app
- `pipe_common/` - shared Python utilities
- `pipeline_scripts/` - helper scripts
- `test_db/` - test DB assets
- `test_publish.py` - publish test
- `ToDo.txt` - notes / backlog

## Run (dev)
```bash
git clone https://github.com/aleksandarv88/project_manager.git
cd project_manager

python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt  # if present
# otherwise: pip install django

cd django_pipeline/vfx_pipeline
python manage.py migrate
python manage.py runserver 127.0.0.1:8002
```

## Houdini publish API (demo)
Set DB env vars (no hardcoded credentials):

```bash
export PM_DB_NAME=FX3X
export PM_DB_USER=postgres
export PM_DB_PASSWORD='your_password'
export PM_DB_HOST=localhost
export PM_DB_PORT=5432
```

`POST /api/publishes/` accepts payload like:

```json
{
  "task_id": 123,
  "item_usd_path": "D:/show/seq/shot/task/usd/item.usd",
  "asset_usd_path": "D:/show/seq/shot/task/usd/asset.usd",
  "source_version": 3,
  "source_iteration": 1,
  "status": "published",
  "preview_path": "D:/show/seq/shot/task/preview/playblast.mov",
  "metadata": {"dcc": "houdini"}
}
```

Auth (demo): local request or matching token.

- Header: `X-PM-Token: <PM_API_TOKEN>`
- Env on server: `PM_API_TOKEN=<same token>`

Houdini helper:

- `pipeline_scripts/houdini/register_publish.py`
- function: `register_publish_to_pm(item_usd_path, asset_usd_path, version=None, iteration=None, status="published")`
