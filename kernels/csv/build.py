#!/usr/bin/env python3
"""Dev build: compile the Aero kernel and refresh `aero_csv/kernel.pyd`."""
import os
import shutil
import subprocess

HERE = os.path.abspath(os.path.dirname(__file__))
EXT = ".pyd" if os.name == "nt" else ".so"
AERO = os.environ.get("AERO", "aero")

subprocess.check_call(
    [AERO, "build", os.path.join("src", "kernel.aero"), "--pyext"], cwd=HERE
)
src = os.path.join(HERE, "src", "kernel" + EXT)
dst = os.path.join(HERE, "aero_csv", "kernel" + EXT)
shutil.copy(src, dst)
print(f"built {dst}")
