import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
# build_exe_options = {"packages": ["os"], "excludes": ["tkinter"]}
build_exe_options = {"packages": ["os"]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = "protect_script",
        version = "0.1",
        description = "The Protector",
        options = {"build_exe": build_exe_options},
        executables = [Executable("160510_Fkraus_Schutz.py", base=base)])