# -*- coding: utf-8 -*-
"""Modelo de datos para un cuadre de caja."""

from dataclasses import dataclass


@dataclass
class Cuadre:
    """Representa un cuadre de caja guardado en la base de datos."""

    id: int
    hora_cuadre: str        # "YYYY-MM-DD HH:MM:SS" desde SQLite
    usuario_id: int
    total_cuadre: float
