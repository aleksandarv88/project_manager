import os
import subprocess
import sys

HOUDINI_EXE = os.environ.get(
    "HOUDINI_EXE",
    r"C:\Program Files\Side Effects Software\Houdini 20.5.512\bin\houdini.exe",
)
TEMPLATE_HIP = os.environ.get("PM_TEMPLATE_HIP", "houdini_templates/usd_pipeline_builder_temp.hip")
HDA_DIR = os.environ.get("PM_HDA_DIR", "")

PM_ROOT = os.environ.get("PM_ROOT", "/path/to/pipeline/root")
PM_SHOW = os.environ.get("PM_SHOW", "DemoShow")
PM_SEQ = sys.argv[1] if len(sys.argv) > 1 else "010"
PM_ACTION = "create_seq"

env = os.environ.copy()
env["PM_ROOT"] = PM_ROOT
env["PM_SHOW"] = PM_SHOW
env["PM_SEQ"] = PM_SEQ
env["PM_ACTION"] = PM_ACTION

# Ensure Houdini finds your HDA
if HDA_DIR:
    env["HOUDINI_OTLSCAN_PATH"] = HDA_DIR + ";" + env.get("HOUDINI_OTLSCAN_PATH", "")

subprocess.Popen([HOUDINI_EXE, TEMPLATE_HIP], env=env)
