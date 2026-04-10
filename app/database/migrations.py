# -*- coding: utf-8 -*-
"""Migraciones de la base de datos.

Cada vez que se agrega una tabla nueva al proyecto, se añade aquí
una función _crear_tabla_<nombre>() y se llama desde run_migrations().
"""

import bcrypt

from app.database.connection import get_connection


def run_migrations() -> None:
    """Ejecuta todas las migraciones en orden y crea datos iniciales."""
    conn = get_connection()
    try:
        _crear_tabla_usuarios(conn)
        _insertar_admin_inicial(conn)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Error ejecutando migraciones: {e}") from e


# ── Tablas ─────────────────────────────────────────────────────────────────────

def _crear_tabla_usuarios(conn) -> None:
    """Crea la tabla de usuarios si no existe."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id           INTEGER  PRIMARY KEY AUTOINCREMENT,
            nombre       TEXT     NOT NULL,
            username     TEXT     UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            rol          TEXT     NOT NULL CHECK(rol IN ('admin', 'cajera')),
            activo       INTEGER  DEFAULT 1,
            creado_en    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)


# ── Datos iniciales ────────────────────────────────────────────────────────────

def _insertar_admin_inicial(conn) -> None:
    """Inserta el usuario administrador predeterminado si no existe."""
    cursor = conn.execute("SELECT id FROM usuarios WHERE username = 'admin'")
    if cursor.fetchone() is not None:
        return  # Ya existe, no hacer nada

    password_hash = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt())
    conn.execute(
        """
        INSERT INTO usuarios (nombre, username, password_hash, rol)
        VALUES (?, ?, ?, ?)
        """,
        ("Administrador", "admin", password_hash.decode("utf-8"), "admin"),
    )
