# -*- mode: python -*-
import os
from distutils.sysconfig import get_python_lib

block_cipher = None

a = Analysis(['pubgis/pubgis.py'],
             pathex=[],
             binaries=[(os.path.join(get_python_lib(), 'cv2', '*.dll'), '.')],
             datas=[('pubgis/images/*.jpg', 'pubgis/images'), ('pubgis/pubgis_gui.ui', 'pubgis')],
             hiddenimports=['numpy'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name='PUBGIS',
          debug=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False)
