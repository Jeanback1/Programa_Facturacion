# -*- coding: utf-8 -*-
"""Modelo de datos para el usuario del sistema."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Usuario:
    """Representa un usuario registrado en la base de datos."""

    id: int
    nombre: str
    username: str
    password_hash: str
    rol: str          # 'admin' | 'cajera'
    activo: int       # 1 = activo, 0 = desactivado
    creado_en: Optional[str]  # DATETIME como string (ISO 8601)

    @property
    def es_admin(self) -> bool:
        """Indica si el usuario tiene rol de administrador."""
        return self.rol == "admin"
