# -*- coding: utf-8 -*-
"""Modelo de datos para productos del catálogo."""

from dataclasses import dataclass, field


@dataclass
class ProductoVariante:
    """Variante opcional de un producto (ej. "Para llevar" / "Para comer aquí").

    Un producto "tiene variantes" si su lista de variantes no está vacía.
    """

    id: int
    producto_id: int
    nombre: str
    precio: float


@dataclass
class Producto:
    """Representa un producto del catálogo."""

    id: int
    nombre: str
    precio: float
    variantes: list[ProductoVariante] = field(default_factory=list)