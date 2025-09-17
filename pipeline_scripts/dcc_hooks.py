from __future__ import annotations

from typing import Optional, Tuple

from . import dcc_saver

try:
    from PySide2 import QtCore, QtWidgets  # type: ignore
except ImportError:  # pragma: no cover
    from PySide6 import QtCore, QtWidgets  # type: ignore


def _resolve_menu_bar() -> Tuple[Optional[object], Optional[QtWidgets.QMenuBar]]:
    import hou

    main_window = hou.qt.mainWindow() or getattr(hou.ui, "mainQtWindow", lambda: None)()
    if main_window is None:
        return None, None

    menu_bar = None
    getter = getattr(main_window, "menuBar", None)
    if callable(getter):
        try:
            candidate = getter()
            if isinstance(candidate, QtWidgets.QMenuBar):
                menu_bar = candidate
        except Exception:
            pass

    if menu_bar is None:
        menu_bar = main_window.findChild(QtWidgets.QMenuBar)

    if menu_bar is None:
        app = QtWidgets.QApplication.instance()
        if app:
            for widget in app.topLevelWidgets():
                if isinstance(widget, QtWidgets.QMenuBar):
                    menu_bar = widget
                    break

    return main_window, menu_bar


def _create_houdini_menu():
    import hou

    main_window, menu_bar = _resolve_menu_bar()
    if menu_bar is None:
        QtCore.QTimer.singleShot(500, _create_houdini_menu)
        return

    existing = menu_bar.findChild(QtWidgets.QMenu, "pipelineMenu")
    if existing:
        menu_bar.removeAction(existing.menuAction())

    pipeline_menu = QtWidgets.QMenu("Pipeline", parent=menu_bar)
    pipeline_menu.setObjectName("pipelineMenu")

    action_version = pipeline_menu.addAction("Save New Version")
    action_version.triggered.connect(dcc_saver.save_new_version)

    action_iteration = pipeline_menu.addAction("Save New Iteration")
    action_iteration.triggered.connect(dcc_saver.save_new_iteration)

    insertion_action = None
    for action in menu_bar.actions():
        label = action.text().strip("&").lower()
        if label == "file":
            insertion_action = action
            break
    if insertion_action is None and menu_bar.actions():
        insertion_action = menu_bar.actions()[0]

    if insertion_action:
        menu_bar.insertMenu(insertion_action, pipeline_menu)
    else:
        menu_bar.addMenu(pipeline_menu)

    if main_window is not None:
        setattr(main_window, "pipeline_menu", pipeline_menu)


def install_houdini_menu() -> None:
    QtCore.QTimer.singleShot(0, _create_houdini_menu)


def install_maya_menu() -> None:
    try:
        import maya.cmds as cmds  # type: ignore
        import maya.utils  # type: ignore
    except ImportError:
        return

    def _create_menu() -> None:
        if cmds.menu("pipelineMenu", exists=True):
            cmds.deleteUI("pipelineMenu", menu=True)
        menu = cmds.menu("pipelineMenu", label="Pipeline", parent="MayaWindow", tearOff=True)
        cmds.menuItem(label="Save New Version", parent=menu, command=lambda *_: dcc_saver.save_new_version())
        cmds.menuItem(label="Save New Iteration", parent=menu, command=lambda *_: dcc_saver.save_new_iteration())

    maya.utils.executeDeferred(_create_menu)
