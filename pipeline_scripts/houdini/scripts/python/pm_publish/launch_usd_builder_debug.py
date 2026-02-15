import os
import subprocess
import sys

HOUDINI_EXE = r"C:\Program Files\Side Effects Software\Houdini 20.5.512\bin\houdini.exe"
TEMPLATE_HIP = r"D:\Work\Houdini\Pipeline_Test\houdini_templates\usd_pipeline_builder_temp.hip"
HDA_DIR = r"D:\pipeline\houdini\otls"

PM_ROOT = r"D:\Work\Houdini\USD"
PM_SHOW = "Test"
PM_SEQ = sys.argv[1] if len(sys.argv) > 1 else "010"
PM_ACTION = "create_seq"

env = os.environ.copy()
env["PM_ROOT"] = PM_ROOT
env["PM_SHOW"] = PM_SHOW
env["PM_SEQ"] = PM_SEQ
env["PM_ACTION"] = PM_ACTION

# Ensure Houdini finds your HDA
#env["HOUDINI_OTLSCAN_PATH"] = HDA_DIR + ";" + env.get("HOUDINI_OTLSCAN_PATH", "")

subprocess.Popen([HOUDINI_EXE, TEMPLATE_HIP], env=env)
