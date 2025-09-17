import os
import sys
from pathlib import Path


def _push_path(path: str | None) -> None:
    if not path or path in sys.path:
        return
    sys.path.append(path)


def _bootstrap() -> None:
    toolkit = os.environ.get("PIPELINE_TOOLKIT_PATH")
    scripts = os.environ.get("PIPELINE_SCRIPTS_PATH")

    if toolkit:
        _push_path(toolkit)
    if scripts:
        _push_path(scripts)

    if toolkit and scripts:
        return

    current = Path(__file__).resolve()
    pipeline_root = current.parent
    project_root = pipeline_root.parent
    _push_path(str(project_root))
    _push_path(str(pipeline_root))


def _install_menu() -> None:
    try:
        import maya.utils  # type: ignore
        import maya.cmds as cmds  # type: ignore
        from pipeline_scripts import dcc_saver
    except Exception:  # noqa: BLE001
        import traceback

        traceback.print_exc()
        return

    def _build() -> None:
        if cmds.menu("pipelineMenu", exists=True):
            cmds.deleteUI("pipelineMenu", menu=True)
        menu = cmds.menu(
            "pipelineMenu",
            label="Pipeline",
            parent="MayaWindow",
            tearOff=True,
        )
        cmds.menuItem(
            label="Save New Version",
            parent=menu,
            command=lambda *_: dcc_saver.save_new_version(),
        )
        cmds.menuItem(
            label="Save New Iteration",
            parent=menu,
            command=lambda *_: dcc_saver.save_new_iteration(),
        )

    maya.utils.executeDeferred(_build)


_bootstrap()
_install_menu()
