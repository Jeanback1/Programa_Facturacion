# -*- coding: utf-8 -*-
"""Repositorio para operaciones CRUD sobre la tabla de usuarios."""

import sqlite3
from typing import Optional

from app.database.connection import get_connection
from app.models.usuario import Usuario


def buscar_por_username(username: str) -> Optional[Usuario]:
    """Busca un usuario activo por su nombre de usuario.

    Retorna None si no existe o está desactivado.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT * FROM usuarios WHERE username = ? AND activo = 1",
            (username,),
        )
        fila = cursor.fetchone()
        return _fila_a_usuario(fila) if fila else None
    except sqlite3.Error as e:
        raise RuntimeError(f"Error buscando usuario '{username}': {e}") from e


def listar_todos() -> list[Usuario]:
    """Retorna todos los usuarios registrados, ordenados por nombre."""
    conn = get_connection()
    try:
        cursor = conn.execute("SELECT * FROM usuarios ORDER BY nombre")
        return [_fila_a_usuario(fila) for fila in cursor.fetchall()]
    except sqlite3.Error as e:
        raise RuntimeError(f"Error listando usuarios: {e}") from e


def crear(nombre: str, username: str, password_hash: str, rol: str) -> Usuario:
    """Inserta un nuevo usuario y retorna el objeto creado."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO usuarios (nombre, username, password_hash, rol)
            VALUES (?, ?, ?, ?)
            """,
            (nombre, username, password_hash, rol),
        )
        conn.commit()
        usuario = _buscar_por_id(cursor.lastrowid, conn)
        if usuario is None:
            raise RuntimeError("No se pudo recuperar el usuario recién creado")
        return usuario
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise RuntimeError(f"El username '{username}' ya existe") from e
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"Error creando usuario '{username}': {e}") from e


def eliminar(id: int) -> None:
    """Elimina permanentemente un usuario por su ID."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM usuarios WHERE id = ?", (id,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"Error eliminando usuario {id}: {e}") from e


def cambiar_estado(id: int, activo: bool) -> None:
    """Activa o desactiva un usuario por su ID."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE usuarios SET activo = ? WHERE id = ?",
            (1 if activo else 0, id),
        )
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"Error cambiando estado del usuario {id}: {e}") from e


# ── Helpers privados ───────────────────────────────────────────────────────────

def _buscar_por_id(id: int, conn) -> Optional[Usuario]:
    """Busca un usuario por ID usando una conexión ya abierta."""
    cursor = conn.execute("SELECT * FROM usuarios WHERE id = ?", (id,))
    fila = cursor.fetchone()
    return _fila_a_usuario(fila) if fila else None


def _fila_a_usuario(fila: sqlite3.Row) -> Usuario:
    """Convierte una fila de la BD al modelo Usuario."""
    return Usuario(
        id=fila["id"],
        nombre=fila["nombre"],
        username=fila["username"],
        password_hash=fila["password_hash"],
        rol=fila["rol"],
        activo=fila["activo"],
        creado_en=fila["creado_en"],
    )
