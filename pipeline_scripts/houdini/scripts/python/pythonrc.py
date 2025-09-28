import os
import sys
from pathlib import Path

def _push_path(value: str | None, *, front: bool = False) -> None:
    if not value:
        return
    if value in sys.path:
        return
    if front:
        sys.path.insert(0, value)
    else:
        sys.path.append(value)

TOOLKIT = os.environ.get("PIPELINE_TOOLKIT_PATH")
HOUDINI_LIB = os.environ.get("PIPELINE_HOUDINI_PYTHON_LIB")
SCRIPTS = os.environ.get("PIPELINE_SCRIPTS_PATH")
os.environ.setdefault("PIPELINE_API_BASE", os.environ.get("API_BASE_URL", "http://127.0.0.1:8000"))

for candidate in (TOOLKIT, SCRIPTS):
    _push_path(candidate, front=False)

if TOOLKIT is None or SCRIPTS is None:
    try:
        current = Path(__file__).resolve()
    except NameError:
        current = None
    if current is not None:
        scripts_dir = str(current.parents[3])
        project_dir = str(current.parents[4])
        os.environ.setdefault("PIPELINE_SCRIPTS_PATH", scripts_dir)
        os.environ.setdefault("PIPELINE_TOOLKIT_PATH", project_dir)
        _push_path(project_dir, front=True)
        _push_path(scripts_dir, front=True)

try:
    if HOUDINI_LIB and HOUDINI_LIB not in sys.path:
        sys.path.insert(0, HOUDINI_LIB)
    else:
        print('[pipeline] Houdini lib already in sys.path or not provided')
    print('[pipeline] HOUDINI_PATH =', os.environ.get('HOUDINI_PATH', ''))
    print('[pipeline] PIPELINE_TOOLKIT_PATH =', os.environ.get('PIPELINE_TOOLKIT_PATH', ''))
    print('[pipeline] PIPELINE_SCRIPTS_PATH =', os.environ.get('PIPELINE_SCRIPTS_PATH', ''))
    print('[pipeline] PYTHONPATH head =', os.environ.get('PYTHONPATH', '').split(os.pathsep)[:5])
    print('[pipeline] sys.path head =', sys.path[:8])
    import psycopg2
    print('[pipeline] psycopg2 module loaded from', psycopg2.__file__)
    from pipeline_scripts import dcc_hooks

    dcc_hooks.install_houdini_menu()
    print("[pipeline] Houdini menu installed")
except Exception:  # noqa: BLE001
    import traceback

    traceback.print_exc()
