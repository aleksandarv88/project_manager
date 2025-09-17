import os
import sys

TOOLKIT = os.environ.get("PIPELINE_TOOLKIT_PATH")
if TOOLKIT and TOOLKIT not in sys.path:
    sys.path.append(TOOLKIT)

try:
    from pipeline_scripts import dcc_hooks
    import maya.utils  # type: ignore

    maya.utils.executeDeferred(dcc_hooks.install_maya_menu)
except Exception:  # noqa: BLE001
    import traceback

    traceback.print_exc()
