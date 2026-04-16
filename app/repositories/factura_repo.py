# -*- coding: utf-8 -*-
"""Repositorio para operaciones sobre la tabla de facturas."""

import sqlite3
from typing import Optional

from app.database.connection import get_connection
from app.models.factura import Factura


def crear(
    total: float,
    usuario_id: int,
    detalle: Optional[str] = None,
    direccion: Optional[str] = None,
) -> Factura:
    """Inserta una nueva factura (sin cuadre) y retorna el objeto creado."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO facturas (total, usuario_id, detalle, direccion) VALUES (?, ?, ?, ?)",
            (total, usuario_id, detalle, direccion),
        )
        conn.commit()
        factura = _buscar_por_id(cursor.lastrowid, conn)
        if factura is None:
            raise RuntimeError("No se pudo recuperar la factura recién creada")
        return factura
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"Error creando factura: {e}") from e


def listar_sin_cuadrar(usuario_id: int) -> list[Factura]:
    """Retorna las facturas del usuario que aún no han sido cuadradas."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            SELECT * FROM facturas
            WHERE cuadre_id IS NULL AND usuario_id = ?
            ORDER BY hora_facturacion DESC
            """,
            (usuario_id,),
        )
        return [_fila_a_factura(fila) for fila in cursor.fetchall()]
    except sqlite3.Error as e:
        raise RuntimeError(f"Error listando facturas sin cuadrar: {e}") from e


# ── Helpers privados ───────────────────────────────────────────────────────────

def _buscar_por_id(id: int, conn) -> Optional[Factura]:
    cursor = conn.execute("SELECT * FROM facturas WHERE id = ?", (id,))
    fila = cursor.fetchone()
    return _fila_a_factura(fila) if fila else None


def _fila_a_factura(fila: sqlite3.Row) -> Factura:
    return Factura(
        id=fila["id"],
        hora_facturacion=fila["hora_facturacion"],
        total=float(fila["total"]),
        usuario_id=fila["usuario_id"],
        cuadre_id=fila["cuadre_id"],
        detalle=fila["detalle"],
        direccion=fila["direccion"],
    )
