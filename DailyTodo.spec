# -*- mode: python ; coding: utf-8 -*-


datas = [
    ('assets/images/1.png', 'assets/images'),
    ('assets/images/2.png', 'assets/images'),
    ('assets/images/3.png', 'assets/images'),
    ('assets/images/4.png', 'assets/images'),
    ('assets/images/5.png', 'assets/images'),
    ('assets/images/5.ico', 'assets/images'),
]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Daily To Do',
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
    icon=['assets\\images\\5.ico'],
)
