# project_manager

Work-in-progress project manager / pipeline prototype.

## Structure
- `django_pipeline/` — Django app
- `pipe_common/` — shared Python utilities
- `pipeline_scripts/` — helper scripts
- `test_db/` — test DB assets
- `test_publish.py` — publish test
- `ToDo.txt` — notes / backlog

## Run (dev)
```bash
git clone https://github.com/aleksandarv88/project_manager.git
cd project_manager

python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt  # if you have it
# otherwise: pip install django

cd django_pipeline
python manage.py migrate
python manage.py runserver
