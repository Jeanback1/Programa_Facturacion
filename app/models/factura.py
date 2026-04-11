# -*- coding: utf-8 -*-
"""Modelo de datos para una factura."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Factura:
    """Representa una factura guardada en la base de datos."""

    id: int
    hora_facturacion: str    # "YYYY-MM-DD HH:MM:SS" desde SQLite
    total: float
    usuario_id: int
    cuadre_id: Optional[int] # None = no cuadrada aún
