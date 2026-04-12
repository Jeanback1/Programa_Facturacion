# -*- coding: utf-8 -*-
"""Vista de facturación — catálogo de productos y lista de la factura actual."""

from collections.abc import Callable

import customtkinter as ctk

from app.models.producto import Producto
from app.repositories import factura_item_repo, factura_repo, producto_repo
from app.session import Session

_CARD_WIDTH: int = 150
_CARD_HEIGHT: int = 100
_CARD_GAP: int = 8


class FacturarView(ctk.CTkFrame):
    """Frame de facturación con catálogo de productos y lista de la factura actual."""

    def __init__(self, master: ctk.CTk, navigate: Callable[[str], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self._navigate = navigate

        master.title("Facturación — Facturar")
        master.geometry("1100x680")
        master.minsize(800, 500)
        master.resizable(True, True)

        # Estado de la factura actual: {product_id: {nombre, precio_unitario, cantidad, label}}
        self._items: dict[int, dict] = {}
        self._total: float = 0.0

        # Productos cargados desde la BD (se usan para filtrar en búsqueda)
        self._todos_productos: list[Producto] = producto_repo.listar_todos()

        # Estado de la cuadrícula del catálogo
        self._productos_actuales: list[Producto] = []
        self._num_columnas: int = 3          # default seguro; se corrige al primer <Configure>
        self._reflow_job: str | None = None  # handle de debounce para resize

        self._construir_ui()
        self._renderizar_catalogo(self._todos_productos)

    def _construir_ui(self) -> None:
        """Construye todos los widgets de la pantalla de facturación."""

        # ── Header ─────────────────────────────────────────────────
        header = ctk.CTkFrame(self, height=56, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkButton(
            header,
            text="←",
            width=48,
            height=36,
            fg_color="transparent",
            border_width=1,
            font=ctk.CTkFont(size=18),
            command=self._volver_a_home,
        ).pack(side="left", padx=16, pady=10)

        # ── Barra de búsqueda (ancho completo) ─────────────────────
        frame_busqueda = ctk.CTkFrame(self, fg_color="transparent")
        frame_busqueda.pack(fill="x", padx=16, pady=(10, 6))

        self._campo_busqueda = ctk.CTkEntry(
            frame_busqueda,
            placeholder_text="Buscar producto...",
            height=40,
            font=ctk.CTkFont(size=14),
        )
        self._campo_busqueda.pack(fill="x", expand=True)
        self._campo_busqueda.bind("<KeyRelease>", lambda _event: self._buscar_producto())

        # ── Área de dos columnas ────────────────────────────────────
        area_columnas = ctk.CTkFrame(self, fg_color="transparent")
        area_columnas.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        area_columnas.grid_columnconfigure(0, weight=7)
        area_columnas.grid_columnconfigure(1, weight=3)
        area_columnas.grid_rowconfigure(0, weight=1)

        # ── Columna izquierda — Catálogo ────────────────────────────
        col_izquierda = ctk.CTkFrame(area_columnas, fg_color="transparent")
        col_izquierda.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        col_izquierda.grid_rowconfigure(0, weight=1)
        col_izquierda.grid_columnconfigure(0, weight=1)

        self._frame_catalogo = ctk.CTkScrollableFrame(
            col_izquierda,
            label_text="Catálogo",
            label_font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._frame_catalogo.grid(row=0, column=0, sticky="nsew")
        self._frame_catalogo._parent_canvas.bind(
            "<Configure>",
            self._on_catalogo_resize,
            add="+",
        )

        # ── Columna derecha — Lista de la factura ───────────────────
        col_derecha = ctk.CTkFrame(area_columnas)
        col_derecha.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        col_derecha.grid_rowconfigure(0, weight=1)
        col_derecha.grid_columnconfigure(0, weight=1)

        self._frame_factura = ctk.CTkScrollableFrame(
            col_derecha,
            label_text="Factura actual",
            label_font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._frame_factura.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 4))

        # Placeholder visible cuando la factura está vacía
        self._placeholder_factura = ctk.CTkLabel(
            self._frame_factura,
            text="Sin productos aún",
            text_color="gray",
            font=ctk.CTkFont(size=13),
        )
        self._placeholder_factura.pack(pady=24)

        # ── Total ───────────────────────────────────────────────────
        frame_total = ctk.CTkFrame(col_derecha, fg_color="transparent")
        frame_total.grid(row=1, column=0, sticky="ew", padx=8, pady=(2, 2))

        ctk.CTkLabel(
            frame_total,
            text="Total:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", padx=12)

        self._label_total = ctk.CTkLabel(
            frame_total,
            text="$0",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#2ECC71",
        )
        self._label_total.pack(side="right", padx=12)

        # ── Botones inferiores ──────────────────────────────────────
        frame_botones = ctk.CTkFrame(col_derecha, fg_color="transparent")
        frame_botones.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 10))
        frame_botones.grid_columnconfigure(0, weight=1)
        frame_botones.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            frame_botones,
            text="Imprimir",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.imprimir_factura,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkButton(
            frame_botones,
            text="Eliminar",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#C0392B",
            hover_color="#922B21",
            command=self._limpiar_factura,
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        # ── Detalle de la factura ───────────────────────────────────
        frame_detalle = ctk.CTkFrame(col_derecha, fg_color="transparent")
        frame_detalle.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 8))

        ctk.CTkLabel(
            frame_detalle,
            text="Detalle:",
            font=ctk.CTkFont(size=13),
        ).pack(anchor="w", padx=4)

        self._entry_detalle = ctk.CTkEntry(
            frame_detalle,
            placeholder_text="Nota opcional...",
            height=36,
        )
        self._entry_detalle.pack(fill="x", padx=4)

    # ── Catálogo ────────────────────────────────────────────────────────────────

    def _on_catalogo_resize(self, event: object) -> None:
        """Debounce del evento <Configure> del canvas del catálogo."""
        if self._reflow_job is not None:
            self.after_cancel(self._reflow_job)
        self._reflow_job = self.after(120, lambda: self._reflow_grid(event.width))

    def _reflow_grid(self, canvas_width: int) -> None:
        """Recalcula columnas y re-renderiza el catálogo si el número cambió."""
        self._reflow_job = None
        cols = max(1, canvas_width // (_CARD_WIDTH + _CARD_GAP))
        if cols != self._num_columnas:
            self._num_columnas = cols
            self._renderizar_catalogo(self._productos_actuales)

    def _renderizar_catalogo(self, productos: list[Producto]) -> None:
        """Limpia el catálogo y lo re-renderiza con la lista de productos dada."""
        self._productos_actuales = productos

        for widget in self._frame_catalogo.winfo_children():
            widget.destroy()

        if not productos:
            ctk.CTkLabel(
                self._frame_catalogo,
                text="No se encontraron productos",
                text_color="gray",
                font=ctk.CTkFont(size=13),
            ).pack(pady=24)
            return

        cols = self._num_columnas

        # Limpiar columnas sobrantes de un layout anterior más ancho
        for c in range(cols, cols + 10):
            self._frame_catalogo.grid_columnconfigure(c, weight=0, minsize=0)
        for c in range(cols):
            self._frame_catalogo.grid_columnconfigure(c, weight=1, minsize=_CARD_WIDTH)

        for idx, producto in enumerate(productos):
            self._crear_tarjeta_producto(producto, row=idx // cols, col=idx % cols)

    def _crear_tarjeta_producto(self, producto: Producto, *, row: int, col: int) -> None:
        """Crea una tarjeta de producto cuadrada en la posición (row, col) del grid."""
        tarjeta = ctk.CTkFrame(
            self._frame_catalogo,
            width=_CARD_WIDTH,
            height=_CARD_HEIGHT,
            corner_radius=8,
            border_width=2,
            border_color='#555555'
        )
        tarjeta.grid(
            row=row, column=col,
            padx=_CARD_GAP // 2, pady=_CARD_GAP // 2,
            sticky="n",
        )
        tarjeta.grid_propagate(False)

        tarjeta.grid_rowconfigure(0, weight=1)   # área del nombre: crece
        tarjeta.grid_rowconfigure(1, weight=0)   # botón: altura fija
        tarjeta.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tarjeta,
            text=producto.nombre,
            font=ctk.CTkFont(size=12, weight="bold"),
            wraplength=_CARD_WIDTH - 16,
            anchor="center",
            justify="center",
        ).grid(row=0, column=0, padx=8, pady=(10, 4), sticky="nsew")

        ctk.CTkButton(
            tarjeta,
            text="Agregar",
            width=_CARD_WIDTH - 24,
            height=30,
            font=ctk.CTkFont(size=12),
            command=lambda p=producto: self._agregar_a_factura(p),
        ).grid(row=1, column=0, padx=12, pady=(0, 10))

    def _buscar_producto(self) -> None:
        """Filtra el catálogo según el texto ingresado en la barra de búsqueda."""
        termino = self._campo_busqueda.get().strip().lower()
        if termino:
            filtrados = [p for p in self._todos_productos if termino in p.nombre.lower()]
        else:
            filtrados = self._todos_productos
        self._renderizar_catalogo(filtrados)

    # ── Factura ─────────────────────────────────────────────────────────────────

    def _agregar_a_factura(self, producto: Producto) -> None:
        """Agrega el producto a la factura o incrementa su cantidad si ya existe."""
        pid = producto.id

        if pid in self._items:
            self._items[pid]["cantidad"] += 1
            item = self._items[pid]
            item["lbl_cantidad"].configure(text=f"{item['cantidad']:g}")
            total = item["precio_unitario"] * item["cantidad"]
            item["lbl_precio"].configure(text=f"${total:,.0f}")
        else:
            # Ocultar el placeholder al agregar el primer ítem
            if not self._items:
                self._placeholder_factura.pack_forget()

            item_frame = ctk.CTkFrame(
                self._frame_factura,
                height=50,
                border_width=1,
                border_color="#555555",
                corner_radius=6
            )
            item_frame.pack(fill="x", padx=8, pady=4)
            item_frame.pack_propagate(False)

            item_frame.grid_columnconfigure(0, weight=0)  # Cantidad
            item_frame.grid_columnconfigure(1, weight=0)  # Botón +
            item_frame.grid_columnconfigure(2, weight=1)  # Nombre
            item_frame.grid_columnconfigure(3, weight=0)  # Precio

            lbl_cantidad = ctk.CTkLabel(
                item_frame,
                text="1",
                font=ctk.CTkFont(size=14, weight="bold"),
                width=40,
            )
            lbl_cantidad.grid(row=0, column=0, padx=(8, 0), pady=4, sticky="w")

            ctk.CTkButton(
                item_frame,
                text="+",
                width=24,
                height=24,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="transparent",
                border_width=1,
                command=lambda p=pid: self._abrir_popup_cantidad(p),
            ).grid(row=0, column=1, padx=4, pady=4)

            ctk.CTkLabel(
                item_frame,
                text=producto.nombre,
                font=ctk.CTkFont(size=14),
                anchor="w",
            ).grid(row=0, column=2, padx=4, pady=4, sticky="ew")

            lbl_precio = ctk.CTkLabel(
                item_frame,
                text=f"${producto.precio:,.0f}",
                font=ctk.CTkFont(size=14, weight="bold"),
                width=80,
                anchor="e",
            )
            lbl_precio.grid(row=0, column=3, padx=8, pady=4, sticky="e")

            self._items[pid] = {
                "nombre": producto.nombre,
                "precio_unitario": producto.precio,
                "cantidad": 1,
                "label": item_frame,
                "lbl_cantidad": lbl_cantidad,
                "lbl_precio": lbl_precio,
            }

        self._total += producto.precio
        self._label_total.configure(text=f"${self._total:,.0f}")

    def _abrir_popup_cantidad(self, pid: int) -> None:
        """Abre un popup para editar la cantidad de un ítem (soporta decimales)."""
        item = self._items[pid]
        raiz = self.winfo_toplevel()

        popup = ctk.CTkToplevel(raiz)
        popup.title("Editar cantidad")
        popup.resizable(False, False)
        popup.transient(raiz)

        ancho, alto = 300, 170
        raiz.update_idletasks()
        x = raiz.winfo_x() + (raiz.winfo_width() - ancho) // 2
        y = raiz.winfo_y() + (raiz.winfo_height() - alto) // 2
        popup.geometry(f"{ancho}x{alto}+{x}+{y}")
        popup.after(50, popup.grab_set)

        ctk.CTkLabel(
            popup,
            text=f"Cantidad — {item['nombre']}",
            font=ctk.CTkFont(size=13, weight="bold"),
            wraplength=260,
        ).pack(pady=(16, 6), padx=16)

        entry = ctk.CTkEntry(popup, width=200)
        entry.insert(0, f"{item['cantidad']:g}")
        entry.pack(pady=4, padx=16)
        entry.focus()

        lbl_error = ctk.CTkLabel(popup, text="", text_color="#FF5555", font=ctk.CTkFont(size=11))
        lbl_error.pack()

        def _confirmar() -> None:
            try:
                nueva = float(entry.get().replace(",", "."))
            except ValueError:
                lbl_error.configure(text="Valor inválido")
                return
            if nueva <= 0:
                lbl_error.configure(text="Debe ser mayor a 0")
                return

            anterior_subtotal = item["precio_unitario"] * item["cantidad"]
            self._total -= anterior_subtotal
            item["cantidad"] = nueva
            nuevo_subtotal = item["precio_unitario"] * nueva
            self._total += nuevo_subtotal

            item["lbl_cantidad"].configure(text=f"{nueva:g}")
            item["lbl_precio"].configure(text=f"${nuevo_subtotal:,.0f}")
            self._label_total.configure(text=f"${self._total:,.0f}")
            popup.destroy()

        ctk.CTkButton(popup, text="Aceptar", width=120, command=_confirmar).pack(pady=(6, 16))
        popup.bind("<Return>", lambda _e: _confirmar())

    def _limpiar_factura(self) -> None:
        """Elimina todos los productos de la factura y resetea el total."""
        for widget in self._frame_factura.winfo_children():
            widget.destroy()

        self._items.clear()
        self._total = 0.0
        self._label_total.configure(text="$0")
        self._entry_detalle.delete(0, "end")

        # Restaurar el placeholder
        self._placeholder_factura = ctk.CTkLabel(
            self._frame_factura,
            text="Sin productos aún",
            text_color="gray",
            font=ctk.CTkFont(size=13),
        )
        self._placeholder_factura.pack(pady=24)

    @staticmethod
    def _texto_item(item: dict) -> str:
        """Formatea una línea de la factura: cantidad - nombre - precio_total."""
        total = item["precio_unitario"] * item["cantidad"]
        return f"{item['cantidad']} - {item['nombre']} - ${total:,.0f}"

    def imprimir_factura(self) -> None:
        """Guarda la factura actual en la base de datos y limpia el formulario."""
        if not self._items:
            self._label_total.configure(text="Sin ítems", text_color="#FF5555")
            self.after(1500, lambda: self._label_total.configure(text="$0", text_color="#2ECC71"))
            return

        usuario_id = Session().usuario_actual.id
        detalle = self._entry_detalle.get().strip() or None
        try:
            factura = factura_repo.crear(total=self._total, usuario_id=usuario_id, detalle=detalle)
            factura_item_repo.crear_items(factura.id, self._items)
        except RuntimeError:
            self._label_total.configure(text="Error al guardar", text_color="#FF5555")
            self.after(
                2000,
                lambda: self._label_total.configure(
                    text=f"${self._total:,.0f}", text_color="#2ECC71"
                ),
            )
            return

        self._limpiar_factura()
        self._label_total.configure(text="Guardada ✓", text_color="#2ECC71")
        self.after(1500, lambda: self._label_total.configure(text="$0"))

    def _volver_a_home(self) -> None:
        """Regresa a la pantalla principal."""
        self._navigate("home")
