#!/usr/bin/env python3
"""Build hook: compile the Aero kernel and bundle the extension into the package.

`pip install .` works when the Aero toolchain is on PATH (or set via the
`AERO` environment variable): this compiles `src/kernel.aero` to a CPython
extension (`.pyd`/`.so`) with `aero build --pyext` and places it inside the
`aero_csv` package.
"""
import os
import shutil
import subprocess

from setuptools import setup
from setuptools.command.build_py import build_py

HERE = os.path.abspath(os.path.dirname(__file__))
EXT = ".pyd" if os.name == "nt" else ".so"


def build_kernel():
    """Compile kernel.aero and drop kernel<EXT> into the source package dir."""
    aero = os.environ.get("AERO", "aero")
    subprocess.check_call(
        [aero, "build", os.path.join("src", "kernel.aero"), "--pyext"],
        cwd=HERE,
    )
    src = os.path.join(HERE, "src", "kernel" + EXT)
    dst = os.path.join(HERE, "aero_csv", "kernel" + EXT)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy(src, dst)
    return dst


class BuildPy(build_py):
    def run(self):
        kernel = build_kernel()
        super().run()  # package the .py files into build_lib
        # Make sure the compiled extension lands next to __init__.py.
        dst = os.path.join(self.build_lib, "aero_csv", os.path.basename(kernel))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy(kernel, dst)


setup(cmdclass={"build_py": BuildPy})
