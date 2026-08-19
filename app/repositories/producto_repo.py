# -*- coding: utf-8 -*-
"""Repositorio de productos — operaciones CRUD sobre la tabla productos y sus variantes."""

from app.database.connection import get_connection
from app.models.producto import Producto, ProductoVariante, GRUPO_GUARNICION, GRUPO_COMER_LLEVAR


def listar_todos() -> list[Producto]:
    """Devuelve todos los productos (con sus variantes) ordenados por nombre."""
    conn = get_connection()
    cursor = conn.execute("SELECT id, nombre, precio FROM productos ORDER BY nombre")
    productos = [_fila_a_producto(fila) for fila in cursor.fetchall()]
    _cargar_variantes(productos, conn)
    return productos


def buscar(termino: str) -> list[Producto]:
    """Devuelve los productos cuyo nombre contenga el término de búsqueda."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT id, nombre, precio FROM productos WHERE nombre LIKE ? ORDER BY nombre",
        (f"%{termino}%",),
    )
    productos = [_fila_a_producto(fila) for fila in cursor.fetchall()]
    _cargar_variantes(productos, conn)
    return productos


def crear(
    nombre: str,
    precio: float,
    guarniciones: list[str] | None = None,
    comer_llevar: list[tuple[str, float]] | None = None,
) -> Producto:
    """Inserta un nuevo producto y devuelve el objeto creado.

    guarniciones: lista opcional de nombres (grupo 1, solo modifica el nombre).
    comer_llevar: lista opcional de (nombre, precio) (grupo 2).
    """
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO productos (nombre, precio) VALUES (?, ?)",
        (nombre, precio),
    )
    producto_id: int = cursor.lastrowid  # type: ignore[assignment]

    filas = []
    filas += [(producto_id, GRUPO_GUARNICION, g, 0.0) for g in (guarniciones or [])]
    filas += [
        (producto_id, GRUPO_COMER_LLEVAR, nombre_v, precio_v)
        for nombre_v, precio_v in (comer_llevar or [])
    ]
    if filas:
        conn.executemany(
            "INSERT INTO producto_variantes (producto_id, grupo, nombre, precio) VALUES (?, ?, ?, ?)",
            filas,
        )
    conn.commit()
    return Producto(
        id=producto_id,
        nombre=nombre,
        precio=precio,
        variantes=_variantes_de(producto_id, conn),
    )


def eliminar(id: int) -> None:
    """Elimina el producto (y sus variantes) con el id dado."""
    conn = get_connection()
    conn.execute("DELETE FROM productos WHERE id = ?", (id,))
    conn.commit()


def _cargar_variantes(productos: list[Producto], conn) -> None:
    """Asigna las variantes de cada producto de la lista en una sola consulta."""
    if not productos:
        return
    ids = [p.id for p in productos]
    placeholders = ",".join("?" * len(ids))
    cursor = conn.execute(
        f"SELECT id, producto_id, grupo, nombre, precio FROM producto_variantes "
        f"WHERE producto_id IN ({placeholders}) ORDER BY grupo, id",
        ids,
    )
    agrupadas: dict[int, list[ProductoVariante]] = {}
    for fila in cursor.fetchall():
        agrupadas.setdefault(fila["producto_id"], []).append(
            ProductoVariante(
                id=fila["id"],
                producto_id=fila["producto_id"],
                nombre=fila["nombre"],
                precio=float(fila["precio"]),
                grupo=int(fila["grupo"]),
            )
        )
    for p in productos:
        p.variantes = agrupadas.get(p.id, [])


def _variantes_de(producto_id: int, conn) -> list[ProductoVariante]:
    """Devuelve las variantes de un producto."""
    cursor = conn.execute(
        "SELECT id, producto_id, grupo, nombre, precio FROM producto_variantes "
        "WHERE producto_id = ? ORDER BY grupo, id",
        (producto_id,),
    )
    return [
        ProductoVariante(
            id=fila["id"],
            producto_id=fila["producto_id"],
            nombre=fila["nombre"],
            precio=float(fila["precio"]),
            grupo=int(fila["grupo"]),
        )
        for fila in cursor.fetchall()
    ]


def _fila_a_producto(fila) -> Producto:
    return Producto(id=fila["id"], nombre=fila["nombre"], precio=float(fila["precio"]))