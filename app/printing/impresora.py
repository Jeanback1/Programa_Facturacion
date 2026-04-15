# -*- coding: utf-8 -*-
"""Módulo de impresión de recibos en impresoras térmicas ESC/POS (Epson TM-T20II)."""

from app.models.factura import Factura

_LINE_WIDTH = 42  # caracteres por línea en papel 80 mm con fuente estándar A


def imprimir_recibo(
    factura: Factura,
    items: dict,
    config: dict[str, str],
    nombre_cajera: str,
    detalle: str | None = None,
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
        _imprimir_cuerpo(p, factura, items, nombre_cajera, detalle)
        _imprimir_pie(p, config)
        p.cut()
    finally:
        p.close()


# ── Secciones del recibo ───────────────────────────────────────────────────────

def _imprimir_encabezado(p, config: dict[str, str]) -> None:
    """Nombre del local (grande, centrado) + datos opcionales."""
    p.set(align="center", bold=True, width=2, height=2)
    p.text(config.get("nombre_local", "Mi Local").upper() + "\n")
    p.set(align="center", bold=False, width=1, height=1)

    for clave, prefijo in [("direccion", ""), ("telefono", "Tel: "), ("rnc", "RNC: ")]:
        valor = config.get(clave, "").strip()
        if valor:
            p.text(prefijo + valor + "\n")

    p.text("\n")


def _imprimir_cuerpo(
    p,
    factura: Factura,
    items: dict,
    nombre_cajera: str,
    detalle: str | None,
) -> None:
    """Número de factura, cajera, líneas de productos, total y nota."""
    p.set(align="left")
    p.text("=" * _LINE_WIDTH + "\n")

    # Hora: quitar la 'T' de ISO si existe, y truncar a "YYYY-MM-DD HH:MM"
    hora = factura.hora_facturacion[:16].replace("T", " ")
    p.text(f"Factura #{factura.id}  {hora}\n")
    p.text(f"Cajera: {nombre_cajera}\n")
    p.text("=" * _LINE_WIDTH + "\n")

    for item in items.values():
        _imprimir_linea_item(p, item)

    p.text("-" * _LINE_WIDTH + "\n")

    # Total en negrita
    total_str = f"${factura.total:,.0f}"
    espacio = _LINE_WIDTH - len(total_str)
    p.set(bold=True)
    p.text(f"{'TOTAL:':<{espacio}}{total_str}\n")
    p.set(bold=False)

    if detalle:
        p.text("=" * _LINE_WIDTH + "\n")
        linea_detalle = f"Nota: {detalle}"
        p.text(linea_detalle[:_LINE_WIDTH] + "\n")


def _imprimir_linea_item(p, item: dict) -> None:
    """Formato: '  2 x Nombre del producto        $1,500'"""
    qty_str = f"{item['cantidad']:g}"
    subtotal = item["precio_unitario"] * item["cantidad"]
    precio_str = f"${subtotal:,.0f}"
    espacio_izq = _LINE_WIDTH - len(precio_str)
    izquierda = f"{qty_str} x {item['nombre']}"
    if len(izquierda) >= espacio_izq:
        izquierda = izquierda[: espacio_izq - 1]
    p.text(f"{izquierda:<{espacio_izq}}{precio_str}\n")


def _imprimir_pie(p, config: dict[str, str]) -> None:
    """Mensaje de cierre centrado."""
    p.text("=" * _LINE_WIDTH + "\n")
    pie = config.get("mensaje_pie", "¡Gracias por su compra!").strip()
    p.set(align="center")
    p.text(pie + "\n\n")
    p.set(align="left")
