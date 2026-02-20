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

def _resolve_scripts_dir_from_paths() -> str | None:
    candidates: list[str] = []
    candidates.extend((os.environ.get("PYTHONPATH") or "").split(os.pathsep))
    candidates.extend(sys.path)
    needle = os.path.normcase(os.path.join("pipeline_scripts", "houdini", "scripts", "python"))
    for raw in candidates:
        if not raw:
            continue
        try:
            p = Path(raw).resolve()
        except Exception:
            continue
        if not p.exists():
            continue
        if needle in os.path.normcase(str(p)):
            for parent in [p, *p.parents]:
                if parent.name == "pipeline_scripts":
                    return str(parent)
    return None

TOOLKIT = os.environ.get("PIPELINE_TOOLKIT_PATH") or ""
HOUDINI_LIB = os.environ.get("PIPELINE_HOUDINI_PYTHON_LIB") or ""
SCRIPTS = os.environ.get("PIPELINE_SCRIPTS_PATH") or ""
os.environ.setdefault("PIPELINE_API_BASE", os.environ.get("API_BASE_URL", "http://127.0.0.1:8002"))

for candidate in (TOOLKIT, SCRIPTS):
    _push_path(candidate, front=False)

if not TOOLKIT or not SCRIPTS:
    scripts_dir = None
    try:
        current = Path(__file__).resolve()
        scripts_dir = str(current.parents[3])
    except Exception:
        scripts_dir = None

    if not scripts_dir:
        scripts_dir = _resolve_scripts_dir_from_paths()

    if scripts_dir:
        project_dir = str(Path(scripts_dir).parent)
        os.environ["PIPELINE_SCRIPTS_PATH"] = scripts_dir
        os.environ["PIPELINE_TOOLKIT_PATH"] = project_dir
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
    # MainMenuCommon.xml already defines the Houdini Pipeline menu.
    # Keep Qt menu injection opt-in to avoid duplicate menus.
    install_qt_menu = (os.environ.get("PIPELINE_INSTALL_QT_MENU") or "").strip().lower() in {"1", "true", "yes"}
    if install_qt_menu:
        try:
            from pipeline_scripts import dcc_hooks
            dcc_hooks.install_houdini_menu()
            print("[pipeline] Houdini Qt menu installed")
        except Exception as exc:
            print(f"[pipeline] Qt menu install skipped: {exc}")
    else:
        print("[pipeline] Using XML menu only (Qt menu injection disabled)")
except Exception:  # noqa: BLE001
    import traceback

    traceback.print_exc()
