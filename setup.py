import sys

from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = dict(packages=[], excludes=[])

base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('pubgis\pubgis_gui.py', base=base, targetName='PUBGIS')
]

setup(name='PUBGIS',
      version='0.1',
      description='',
      options=dict(build_exe=buildOptions),
      executables=executables)
