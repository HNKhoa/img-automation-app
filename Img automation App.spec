# -*- mode: python ; coding: utf-8 -*-
# AUTO-RENDERED by tools/build_specs.py - do not hand-edit individual specs.

from PyInstaller.utils.hooks import collect_all, collect_submodules

cffi_datas, cffi_binaries, cffi_hiddenimports = collect_all('curl_cffi')
modes_hiddenimports = collect_submodules('backend.modes')

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=cffi_binaries,
    datas=[('frontend', 'frontend'), ('.env.example', '.'), *cffi_datas],
    hiddenimports=[
        *cffi_hiddenimports,
        *modes_hiddenimports,
        'curl_cffi', '_cffi_backend',
        'PIL', 'PIL.Image', 'PIL.ImageOps',
        'webview', 'webview.platforms.winforms',
        
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Img automation App',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)


