# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_all

# Datos de escpos y customtkinter
datas  = collect_data_files('escpos')
datas += collect_data_files('customtkinter')

a = Analysis(
    ['main.py'],
    pathex=['/home/jean/work/programas/Programa_Facturacion'],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'escpos',
        'escpos.printer',
        'escpos.capabilities',
        'customtkinter',
        'bcrypt',
        'PIL',
        'tkinter',
        '_tkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['win32print', 'win32ui'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Facturacion',
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
    icon=None,
)
