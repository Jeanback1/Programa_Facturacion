# -*- coding: utf-8 -*-
"""Repositorio para operaciones sobre la tabla de ítems de factura."""

import sqlite3

from app.database.connection import get_connection
from app.models.factura_item import FacturaItem


def crear_items(factura_id: int, items: dict) -> None:
    """Inserta todos los ítems de una factura en bloque.

    El dict items viene de FacturarView._items:
    {producto_id: {nombre, precio_unitario, cantidad, label}}
    La clave 'label' (widget CTK) se ignora.
    """
    conn = get_connection()
    try:
        filas = [
            (
                factura_id,
                v["nombre"],
                v["precio_unitario"],
                v["cantidad"],
                v["precio_unitario"] * v["cantidad"],
            )
            for v in items.values()
        ]
        conn.executemany(
            """
            INSERT INTO factura_items (factura_id, nombre, precio_unitario, cantidad, subtotal)
            VALUES (?, ?, ?, ?, ?)
            """,
            filas,
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"Error guardando ítems de factura: {e}") from e


def listar_por_factura(factura_id: int) -> list[FacturaItem]:
    """Retorna todos los ítems de una factura, ordenados por id."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM factura_items WHERE factura_id = ? ORDER BY id",
            (factura_id,),
        )
        return [_fila_a_factura_item(fila) for fila in cursor.fetchall()]
    except sqlite3.Error as e:
        raise RuntimeError(f"Error listando ítems de factura {factura_id}: {e}") from e


# ── Helpers privados ───────────────────────────────────────────────────────────

def _fila_a_factura_item(fila: sqlite3.Row) -> FacturaItem:
    return FacturaItem(
        id=fila["id"],
        factura_id=fila["factura_id"],
        nombre=fila["nombre"],
        precio_unitario=float(fila["precio_unitario"]),
        cantidad=fila["cantidad"],
        subtotal=float(fila["subtotal"]),
    )
