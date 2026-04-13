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
        _crear_tabla_productos(conn)
        _crear_tabla_cuadres(conn)
        _crear_tabla_facturas(conn)
        _crear_tabla_factura_items(conn)
        _crear_tabla_configuracion(conn)
        _insertar_admin_inicial(conn)
        _insertar_config_inicial(conn)
        columnas = {fila[1] for fila in conn.execute("PRAGMA table_info(facturas)")}
        if "detalle" not in columnas:
            conn.execute("ALTER TABLE facturas ADD COLUMN detalle TEXT")
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


def _crear_tabla_productos(conn) -> None:
    """Crea la tabla de productos si no existe."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre  TEXT    NOT NULL,
            precio  REAL    NOT NULL CHECK(precio >= 0)
        )
    """)


def _crear_tabla_cuadres(conn) -> None:
    """Crea la tabla de cuadres si no existe."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cuadres (
            id           INTEGER  PRIMARY KEY AUTOINCREMENT,
            hora_cuadre  DATETIME DEFAULT CURRENT_TIMESTAMP,
            usuario_id   INTEGER  NOT NULL REFERENCES usuarios(id),
            total_cuadre REAL     NOT NULL CHECK(total_cuadre >= 0)
        )
    """)


def _crear_tabla_facturas(conn) -> None:
    """Crea la tabla de facturas si no existe."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS facturas (
            id               INTEGER  PRIMARY KEY AUTOINCREMENT,
            hora_facturacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            total            REAL     NOT NULL CHECK(total >= 0),
            usuario_id       INTEGER  NOT NULL REFERENCES usuarios(id),
            cuadre_id        INTEGER  REFERENCES cuadres(id)
        )
    """)


def _crear_tabla_factura_items(conn) -> None:
    """Crea la tabla de ítems de factura si no existe."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS factura_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            factura_id      INTEGER NOT NULL REFERENCES facturas(id),
            nombre          TEXT    NOT NULL,
            precio_unitario REAL    NOT NULL CHECK(precio_unitario >= 0),
            cantidad        INTEGER NOT NULL CHECK(cantidad > 0),
            subtotal        REAL    NOT NULL CHECK(subtotal >= 0)
        )
    """)


def _crear_tabla_configuracion(conn) -> None:
    """Crea la tabla de configuración clave-valor si no existe."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS configuracion (
            clave TEXT PRIMARY KEY,
            valor TEXT NOT NULL DEFAULT ''
        )
    """)


def _insertar_config_inicial(conn) -> None:
    """Inserta los valores predeterminados de configuración si no existen."""
    defaults = [
        ("nombre_local",     "Mi Local"),
        ("direccion",        ""),
        ("telefono",         ""),
        ("rnc",              ""),
        ("mensaje_pie",      "¡Gracias por su compra!"),
        ("impresora_nombre", "EPSON TM-T20II"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO configuracion (clave, valor) VALUES (?, ?)",
        defaults,
    )


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
