# -*- coding: utf-8 -*-
"""Módulo de impresión de recibos en impresoras térmicas ESC/POS (Epson TM-T20II)."""

import textwrap

from app.models.factura import Factura

_LINE_WIDTH = 42  # caracteres por línea en papel 80 mm con fuente estándar A


def imprimir_recibo(
    factura: Factura,
    items: dict,
    config: dict[str, str],
    nombre_cajera: str,
    detalle: str | None = None,
    direccion: str | None = None,
    es_copia: bool = False,
) -> None:
    """Envía el recibo a la impresora térmica configurada en Windows.

    Raises RuntimeError si la impresora no está configurada o no es accesible.
    """
    from escpos.printer import Win32Raw

    nombre_impresora = config.get("impresora_nombre", "").strip()
    if not nombre_impresora:
        raise RuntimeError(
            "No hay impresora configurada. "
            "Configure el nombre en Configuración → Impresora."
        )

    p = Win32Raw(nombre_impresora)
    try:
        _imprimir_encabezado(p, config)
        _imprimir_cuerpo(p, factura, items, nombre_cajera, detalle, direccion, es_copia=es_copia)
        _imprimir_pie(p, config)
        p.cut()
    finally:
        p.close()


# ── Secciones del recibo ───────────────────────────────────────────────────────

def _imprimir_encabezado(p, config: dict[str, str]) -> None:
    """Nombre del local centrado entre separadores + datos opcionales."""
    p.set(align="left")
    p.text("-" * _LINE_WIDTH + "\n")
    p.set(align="center", bold=True)
    p.text(config.get("nombre_local", "Mi Local").upper() + "\n")
    p.set(align="center", bold=False)
    p.text("-" * _LINE_WIDTH + "\n")

    for clave, prefijo in [("direccion", ""), ("telefono", "Tel: "), ("rnc", "RNC: ")]:
        valor = config.get(clave, "").strip()
        if valor:
            p.text(prefijo + valor + "\n")

    p.text("\n")
    p.set(align="left")


def _imprimir_cuerpo(
    p,
    factura: Factura,
    items: dict,
    nombre_cajera: str,
    detalle: str | None,
    direccion: str | None = None,
    es_copia: bool = False,
) -> None:
    """Número de factura, cajera, líneas de productos, total y nota."""
    # ── Datos de la transacción ────────────────────────────────────────────────
    p.set(align="left")
    p.text("-" * _LINE_WIDTH + "\n")

    # Hora: quitar la 'T' de ISO si existe, y truncar a "YYYY-MM-DD HH:MM"
    ts = factura.hora_facturacion[:16].replace("T", " ")
    fecha, hora_str = ts[:10], ts[11:16]
    p.text(f"No. Factura:  {factura.id}\n")
    p.text(f"Cajera:       {nombre_cajera}\n")
    p.text(f"Fecha:        {fecha}   {hora_str}\n")
    if direccion:
        for linea in _wrap_campo("Dirección:    ", direccion):
            p.text(linea + "\n")
    p.text("\n")

    # ── Separador IMPRESION ────────────────────────────────────────────────────
    titulo = " REIMPRESION " if es_copia else " IMPRESION "
    relleno = "*" * ((_LINE_WIDTH - len(titulo)) // 2)
    p.text(f"{relleno}{titulo}{relleno}\n")
    p.text("\n")

    # ── Bloque FACTURA CONTADO ─────────────────────────────────────────────────
    p.text("-" * _LINE_WIDTH + "\n")
    p.set(align="center", bold=True)
    p.text("FACTURA CONTADO\n")
    p.set(align="left", bold=False)
    p.text("-" * _LINE_WIDTH + "\n")
    p.text("\n")

    # ── Líneas de productos ────────────────────────────────────────────────────
    for item in items.values():
        _imprimir_linea_item(p, item)
    p.text("\n")

    # ── Total ──────────────────────────────────────────────────────────────────
    p.text("-" * _LINE_WIDTH + "\n")
    n = len(items)
    articulos_str = f"{n} artículo{'s' if n != 1 else ''}"
    p.text(f"{articulos_str:>{_LINE_WIDTH}}\n")
    total_str = f"${factura.total:,.0f}"
    espacio = _LINE_WIDTH - len(total_str)
    p.set(bold=True)
    p.text(f"{'TOTAL:':<{espacio}}{total_str}\n")
    p.set(bold=False)
    p.text("\n")

    # ── Nota opcional ─────────────────────────────────────────────────────────
    if detalle:
        p.text("-" * _LINE_WIDTH + "\n")
        for linea in _wrap_campo("Nota: ", detalle):
            p.text(linea + "\n")
        p.text("\n")


def _imprimir_linea_item(p, item: dict) -> None:
    """Formato: '2 x Nombre del producto        $1,500' + precio unitario si qty > 1."""
    qty_str = f"{item['cantidad']:g}"
    subtotal = item["precio_unitario"] * item["cantidad"]
    precio_str = f"${subtotal:,.0f}"
    espacio_izq = _LINE_WIDTH - len(precio_str)
    izquierda = f"{qty_str} x {item['nombre']}"
    if len(izquierda) >= espacio_izq:
        izquierda = izquierda[: espacio_izq - 1]
    p.text(f"{izquierda:<{espacio_izq}}{precio_str}\n")

    if item["cantidad"] > 1:
        p.text(f"    @ ${item['precio_unitario']:,.0f} c/u\n")


def _wrap_campo(label: str, texto: str) -> list[str]:
    indent = " " * len(label)
    lineas = textwrap.wrap(texto, _LINE_WIDTH - len(label))
    if not lineas:
        return [label]
    return [label + lineas[0]] + [indent + l for l in lineas[1:]]


def _imprimir_pie(p, config: dict[str, str]) -> None:
    """Mensaje de cierre centrado."""
    p.text("=" * _LINE_WIDTH + "\n")
    pie = config.get("mensaje_pie", "¡Gracias por su compra!").strip()
    p.set(align="center")
    p.text(pie + "\n\n")
    p.set(align="left")


# ── Reporte de cuadre ─────────────────────────────────────────────────────────

def imprimir_cuadre(
    facturas: list,
    cuadre_id: int,
    hora_cuadre: str,
    nombre_cajera: str,
    config: dict[str, str],
    total: float,
) -> None:
    """Imprime el reporte de cuadre en la impresora térmica configurada.

    Raises RuntimeError si la impresora no está configurada o no es accesible.
    """
    from escpos.printer import Win32Raw

    nombre_impresora = config.get("impresora_nombre", "").strip()
    if not nombre_impresora:
        raise RuntimeError(
            "No hay impresora configurada. "
            "Configure el nombre en Configuración → Impresora."
        )

    p = Win32Raw(nombre_impresora)
    try:
        _imprimir_encabezado(p, config)
        _imprimir_cuerpo_cuadre(p, facturas, cuadre_id, hora_cuadre, nombre_cajera, total)
        _imprimir_pie(p, config)
        p.cut()
    finally:
        p.close()


def _imprimir_cuerpo_cuadre(
    p,
    facturas: list,
    cuadre_id: int,
    hora_cuadre: str,
    nombre_cajera: str,
    total: float,
) -> None:
    """Título, datos del cuadre, lista de facturas y total."""
    p.set(align="left")
    p.text("-" * _LINE_WIDTH + "\n")
    p.set(align="center", bold=True)
    p.text("REPORTE DE CUADRE\n")
    p.set(align="left", bold=False)
    p.text("-" * _LINE_WIDTH + "\n")

    ts = hora_cuadre[:16].replace("T", " ")
    fecha, hora_str = ts[:10], ts[11:16]
    p.text(f"Cuadre No.:   {cuadre_id}\n")
    p.text(f"Cajera:       {nombre_cajera}\n")
    p.text(f"Fecha:        {fecha}   {hora_str}\n")
    p.text("\n")

    # ── Encabezado de tabla ────────────────────────────────────────────────────
    p.text("-" * _LINE_WIDTH + "\n")
    col_id = 8    # "#NNN    "
    col_hora = 7  # "HH:MM  "
    col_total = _LINE_WIDTH - col_id - col_hora
    encabezado = f"{'#Fact':<{col_id}}{'Hora':<{col_hora}}{'Total':>{col_total}}"
    p.text(encabezado + "\n")
    p.text("-" * _LINE_WIDTH + "\n")

    # ── Filas de facturas ──────────────────────────────────────────────────────
    for factura in facturas:
        hora_fact = factura.hora_facturacion[11:16]
        total_str = f"${factura.total:,.0f}"
        id_str = f"#{factura.id}"
        fila = f"{id_str:<{col_id}}{hora_fact:<{col_hora}}{total_str:>{col_total}}"
        p.text(fila + "\n")

    p.text("\n")

    # ── Resumen ────────────────────────────────────────────────────────────────
    p.text("-" * _LINE_WIDTH + "\n")
    n = len(facturas)
    p.text(f"  {n} factura{'s' if n != 1 else ''}\n")
    total_str = f"${total:,.0f}"
    espacio = _LINE_WIDTH - len(total_str)
    p.set(bold=True)
    p.text(f"{'TOTAL:':<{espacio}}{total_str}\n")
    p.set(bold=False)
    p.text("\n")
