import os
import subprocess

HOUDINI_EXE = os.environ.get(
    "HOUDINI_EXE",
    r"C:\Program Files\Side Effects Software\Houdini 21.0.512\bin\houdini.exe",
)
TEMPLATE_HIP = os.environ.get(
    "PM_TEMPLATE_HIP",
    os.path.join(os.path.dirname(__file__), "usd_pipeline_builder_temp.hip"),
)

PM_HDA_NODE = os.environ.get("PM_HDA_NODE", "/stage/usd_pipeline_builder1")
PM_BUTTONS = os.environ.get(
    "PM_BUTTONS",
    "create_seq,create_shot,update_seq,create_dep,update_shot,create_artist,update_dep,create_asset,update_artist",
)

PM_ROOT = os.environ.get("PM_ROOT", "/path/to/pipeline/root")
PM_SHOW = os.environ.get("PM_SHOW", "DemoShow")
PM_SEQ = os.environ.get("PM_SEQ", "010")
PM_SHOT = os.environ.get("PM_SHOT", "0010")
PM_DEP = os.environ.get("PM_DEP", "fx")
PM_ARTIST = os.environ.get("PM_ARTIST", "artist01")
PM_TASK = os.environ.get("PM_TASK", "task01")
PM_ASSET = os.environ.get("PM_ASSET", "asset01")

env = os.environ.copy()

# gate for 456.py
env["PM_RUN_USD_BUILDER"] = "1"

# what to press
env["PM_HDA_NODE"] = PM_HDA_NODE
env["PM_BUTTONS"]  = PM_BUTTONS

# context
env["PM_ROOT"]   = PM_ROOT
env["PM_SHOW"]   = PM_SHOW
env["PM_SEQ"]    = PM_SEQ
env["PM_SHOT"]   = PM_SHOT
env["PM_DEP"]    = PM_DEP
env["PM_ARTIST"] = PM_ARTIST
env["PM_TASK"]   = PM_TASK
env["PM_ASSET"]  = PM_ASSET

# optional strict hip check (only if you used it in 456.py)
env["PM_TEMPLATE_HIP"] = TEMPLATE_HIP

subprocess.Popen([HOUDINI_EXE, TEMPLATE_HIP], env=env)
