# -*- coding: utf-8 -*-
"""Repositorio para operaciones sobre la tabla de cuadres."""

import sqlite3

from app.database.connection import get_connection
from app.models.cuadre import Cuadre


def listar_por_usuario(usuario_id: int) -> list[Cuadre]:
    """Retorna todos los cuadres del usuario, del más reciente al más antiguo."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM cuadres WHERE usuario_id = ? ORDER BY hora_cuadre DESC",
            (usuario_id,),
        )
        return [_fila_a_cuadre(fila) for fila in cursor.fetchall()]
    except sqlite3.Error as e:
        raise RuntimeError(f"Error listando cuadres del usuario {usuario_id}: {e}") from e


# ── Helpers privados ───────────────────────────────────────────────────────────

def _fila_a_cuadre(fila: sqlite3.Row) -> Cuadre:
    return Cuadre(
        id=fila["id"],
        hora_cuadre=fila["hora_cuadre"],
        usuario_id=fila["usuario_id"],
        total_cuadre=float(fila["total_cuadre"]),
    )
