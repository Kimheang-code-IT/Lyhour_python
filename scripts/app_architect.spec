# PyInstaller spec for KIEC ENGINEERING & CONSULTING (.exe with Logo icon)
# Run: python scripts/build_exe.py  (creates Logo.ico and runs this spec)

import os
import sys

block_cipher = None
project_root = os.path.abspath(os.path.join(SPECPATH, '..'))

# Bundle app/assets (images, icons, road.jpg, etc.) for runtime
assets_src = os.path.join(project_root, 'app', 'assets')
datas = [(assets_src, 'app/assets')]

# Include Logo.ico in datas so it's available; use as exe icon on Windows
logo_ico = os.path.join(project_root, 'app', 'assets', 'icon', 'Logo.ico')
if sys.platform == 'win32' and os.path.isfile(logo_ico):
    icon = logo_ico
else:
    icon = None

a = Analysis(
    [os.path.join(project_root, 'app', 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'reportlab',
        'reportlab.lib',
        'reportlab.lib.colors',
        'reportlab.lib.pagesizes',
        'reportlab.lib.styles',
        'reportlab.lib.units',
        'reportlab.platypus',
        'fitz',
        'pymupdf',
        'qfluentwidgets',
        'qtawesome',
        'loguru',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['cv2', 'opencv'],  # Not used by this app; avoids NumPy 1.x/2.x conflict
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# --onedir: faster startup; output in dist/KIEC Engineering Consulting/
exe = EXE(
    pyz,
    a.scripts,
    [],
    name='KIEC Engineering Consulting',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
    onefile=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='KIEC Engineering Consulting',
    strip=False,
    upx=True,
    upx_exclude=[],
)
