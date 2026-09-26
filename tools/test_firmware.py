#!/usr/bin/env python3
"""Compile/run the actual diagnostic core against a fake bus, without a board."""
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
FW = ROOT / 'firmware/bringup'

def main():
    with tempfile.TemporaryDirectory(prefix='cc1101-host-tests-') as directory:
        executable = str(Path(directory) / 'diagnostics-test')
        subprocess.run([
            os.environ.get('CXX', 'c++'), '-std=c++11', '-Wall', '-Wextra',
            '-Werror', '-pedantic', '-UNDEBUG', '-I', str(FW / 'include'),
            str(FW / 'tests/diagnostics_test.cpp'), '-o', executable,
        ], check=True)
        subprocess.run([executable], check=True, timeout=10)
        subprocess.run([
            os.environ.get('CXX','c++'),'-std=c++11','-Wall','-Wextra','-Werror',
            '-pedantic','-UNDEBUG','-I',str(FW/'include'),
            str(FW/'tests/rf_boot_test.cpp'),'-o',executable],check=True)
        subprocess.run([executable],check=True,timeout=10)

if __name__ == '__main__':
    main()
