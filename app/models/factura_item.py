# -*- coding: utf-8 -*-
"""Modelo de datos para un ítem dentro de una factura."""

from dataclasses import dataclass


@dataclass
class FacturaItem:
    """Representa un ítem de una factura guardado en la base de datos."""

    id: int
    factura_id: int
    nombre: str             # snapshot del nombre al momento de la venta
    precio_unitario: float
    cantidad: int
    subtotal: float
