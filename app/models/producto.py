# -*- coding: utf-8 -*-
"""Modelo de datos para productos del catálogo."""

from dataclasses import dataclass


@dataclass
class Producto:
    """Representa un producto del catálogo."""

    id: int
    nombre: str
    precio: float
