# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files

# ── Datos de python-escpos y customtkinter ─────────────────────────────────────
# collect_data_files('escpos') recoge capabilities.json; además lo forzamos
# explícito por ruta, por si en otra versión de escpos el hook se comporta
# distinto (defensa contra el error "No such file: escpos/capabilities.json").
datas  = collect_data_files('escpos')
datas += collect_data_files('customtkinter')

try:
    import escpos
    _escpos_dir = os.path.dirname(escpos.__file__)
    _capabilities = os.path.join(_escpos_dir, 'capabilities.json')
    if os.path.isfile(_capabilities):
        # (origen, destino_en_el_EXE) → destino 'escpos' lo coloca en
        # _MEIPASS/escpos/capabilities.json que es donde escpos lo busca.
        datas.append((_capabilities, 'escpos'))
except Exception:
    pass

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'customtkinter',
        'escpos',
        'escpos.printer',
        'escpos.capabilities',
        'win32print',
        'win32ui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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