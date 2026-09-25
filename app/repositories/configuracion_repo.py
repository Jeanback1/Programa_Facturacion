# -*- coding: utf-8 -*-
"""Repositorio para la tabla de configuracion (clave-valor)."""

import sqlite3
from typing import Optional

from app.database.connection import get_connection


def get(clave: str) -> Optional[str]:
    """Retorna el valor de una clave de configuración, o None si no existe."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT valor FROM configuracion WHERE clave = ?", (clave,)
        )
        fila = cursor.fetchone()
        return fila["valor"] if fila else None
    except sqlite3.Error as e:
        raise RuntimeError(f"Error leyendo configuración '{clave}': {e}") from e


def set(clave: str, valor: str) -> None:
    """Inserta o actualiza un valor de configuración."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO configuracion (clave, valor) VALUES (?, ?)",
            (clave, valor),
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"Error guardando configuración '{clave}': {e}") from e


def get_all() -> dict[str, str]:
    """Retorna todas las claves de configuración como diccionario."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT clave, valor FROM configuracion")
        return {fila["clave"]: (fila["valor"] or "") for fila in cursor.fetchall()}
    except sqlite3.Error as e:
        raise RuntimeError(f"Error leyendo configuración: {e}") from e
