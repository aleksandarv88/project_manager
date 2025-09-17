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
SCRIPTS = os.environ.get("PIPELINE_SCRIPTS_PATH")
MAYA_LIB = os.environ.get("PIPELINE_MAYA_PYTHON_LIB")

for candidate in (TOOLKIT, SCRIPTS, MAYA_LIB):
    _push_path(candidate)

if TOOLKIT is None or SCRIPTS is None:
    try:
        current = Path(__file__).resolve()
    except Exception:
        current = None
    if current is not None:
        scripts_dir = str(current.parent.parent)
        project_dir = str(Path(scripts_dir).parent)
        os.environ.setdefault("PIPELINE_SCRIPTS_PATH", scripts_dir)
        os.environ.setdefault("PIPELINE_TOOLKIT_PATH", project_dir)
        _push_path(project_dir, front=True)
        _push_path(scripts_dir, front=True)

print('[pipeline][maya] PYTHONPATH =', os.environ.get('PYTHONPATH', ''))
print('[pipeline][maya] sys.path head =', sys.path[:10])

try:
    from pipeline_scripts import dcc_hooks
    import maya.utils  # type: ignore

    maya.utils.executeDeferred(dcc_hooks.install_maya_menu)
except Exception:  # noqa: BLE001
    import traceback

    traceback.print_exc()
