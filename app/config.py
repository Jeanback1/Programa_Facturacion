# -*- coding: utf-8 -*-
"""Configuración global de la aplicación."""

import sys
from pathlib import Path

APP_VERSION = "1.0.0"
APP_NAME = "Facturación"

# Detectar si corre como ejecutable compilado (.exe) o como script normal
IS_FROZEN = getattr(sys, "frozen", False)

if IS_FROZEN:
    # Ejecutando como binario empaquetado (PyInstaller)
    BASE_DIR = Path(sys.executable).parent
else:
    # Ejecutando como script — sube dos niveles desde app/config.py
    BASE_DIR = Path(__file__).parent.parent

# Directorio de datos según el sistema operativo
if sys.platform == "win32":
    # Windows: AppData\Local\Facturacion\
    _data_dir = Path.home() / "AppData" / "Local" / "Facturacion"
else:
    # Linux/macOS: ~/.local/share/facturacion/
    _data_dir = Path.home() / ".local" / "share" / "facturacion"

# Crear el directorio si no existe (se ejecuta al importar el módulo)
_data_dir.mkdir(parents=True, exist_ok=True)

DB_PATH = _data_dir / "data.db"
