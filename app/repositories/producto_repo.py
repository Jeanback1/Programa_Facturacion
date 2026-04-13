# -*- coding: utf-8 -*-
"""Repositorio de productos — operaciones CRUD sobre la tabla productos."""

from app.database.connection import get_connection
from app.models.producto import Producto


def listar_todos() -> list[Producto]:
    """Devuelve todos los productos ordenados por nombre."""
    conn = get_connection()
    cursor = conn.execute("SELECT id, nombre, precio FROM productos ORDER BY nombre")
    return [_fila_a_producto(fila) for fila in cursor.fetchall()]


def buscar(termino: str) -> list[Producto]:
    """Devuelve los productos cuyo nombre contenga el término de búsqueda."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT id, nombre, precio FROM productos WHERE nombre LIKE ? ORDER BY nombre",
        (f"%{termino}%",),
    )
    return [_fila_a_producto(fila) for fila in cursor.fetchall()]


def crear(nombre: str, precio: float) -> Producto:
    """Inserta un nuevo producto y devuelve el objeto creado."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO productos (nombre, precio) VALUES (?, ?)",
        (nombre, precio),
    )
    conn.commit()
    return Producto(id=cursor.lastrowid, nombre=nombre, precio=precio)


def eliminar(id: int) -> None:
    """Elimina el producto con el id dado."""
    conn = get_connection()
    conn.execute("DELETE FROM productos WHERE id = ?", (id,))
    conn.commit()


def _fila_a_producto(fila) -> Producto:
    return Producto(id=fila["id"], nombre=fila["nombre"], precio=float(fila["precio"]))
