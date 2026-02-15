import os
import subprocess

# ---- EDIT THESE ----
HOUDINI_EXE   = r"C:\Program Files\Side Effects Software\Houdini 21.0.512\bin\houdini.exe"
TEMPLATE_HIP  = r"D:\Work\Houdini\Pipeline_Test\houdini_templates\usd_pipeline_builder_temp.hip"

PM_HDA_NODE   = "/stage/usd_pipeline_builder1"
PM_BUTTONS    = "create_seq,create_shot,update_seq,create_dep,update_shot,create_artist,update_dep,create_asset,update_artist"  # example

PM_ROOT  = r"D:\Work\Houdini\USD"
PM_SHOW  = "Test"
PM_SEQ   = "010"
PM_SHOT  = "0500"
PM_DEP   = "fx"
PM_ARTIST= "Artist01"
PM_TASK  = "PinchIn"
PM_ASSET = "PinchIn"
# --------------------

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
