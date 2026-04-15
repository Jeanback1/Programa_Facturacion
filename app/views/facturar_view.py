# -*- coding: utf-8 -*-
"""Vista de facturación — catálogo de productos y lista de la factura actual."""

from collections.abc import Callable

import customtkinter as ctk

from app.models.producto import Producto
from app.printing import impresora
from app.repositories import configuracion_repo, factura_item_repo, factura_repo, producto_repo
from app.session import Session


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

        # Tamaños ajustables del catálogo
        self._card_width: int = 150
        self._card_height: int = 100
        self._card_gap: int = 8

        # Tamaños ajustables de los ítems de la factura
        self._item_height: int = 50
        self._item_font_size: int = 14

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
            placeholder_text="Buscar por nombre o #id...",
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
        col_izquierda.grid_rowconfigure(0, weight=0)
        col_izquierda.grid_rowconfigure(1, weight=1)
        col_izquierda.grid_columnconfigure(0, weight=1)

        header_cat = ctk.CTkFrame(col_izquierda, height=32, fg_color="transparent")
        header_cat.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        header_cat.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header_cat,
            text="Catálogo",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=(4, 0), sticky="w")

        ctk.CTkButton(
            header_cat,
            text="−",
            width=24, height=24,
            fg_color="transparent",
            border_width=1,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._reducir_catalogo,
        ).grid(row=0, column=2, padx=(0, 2))

        ctk.CTkButton(
            header_cat,
            text="+",
            width=24, height=24,
            fg_color="transparent",
            border_width=1,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._aumentar_catalogo,
        ).grid(row=0, column=3, padx=(0, 4))

        self._frame_catalogo = ctk.CTkScrollableFrame(col_izquierda)
        self._frame_catalogo.grid(row=1, column=0, sticky="nsew")
        self._frame_catalogo._parent_canvas.bind(
            "<Configure>",
            self._on_catalogo_resize,
            add="+",
        )

        # ── Columna derecha — Lista de la factura ───────────────────
        col_derecha = ctk.CTkFrame(area_columnas)
        col_derecha.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        col_derecha.grid_rowconfigure(0, weight=0)
        col_derecha.grid_rowconfigure(1, weight=1)
        col_derecha.grid_columnconfigure(0, weight=1)

        header_fac = ctk.CTkFrame(col_derecha, height=32, fg_color="transparent")
        header_fac.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 2))
        header_fac.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header_fac,
            text="Factura actual",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, padx=(4, 0), sticky="w")

        ctk.CTkButton(
            header_fac,
            text="−",
            width=24, height=24,
            fg_color="transparent",
            border_width=1,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._reducir_factura,
        ).grid(row=0, column=2, padx=(0, 2))

        ctk.CTkButton(
            header_fac,
            text="+",
            width=24, height=24,
            fg_color="transparent",
            border_width=1,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._aumentar_factura,
        ).grid(row=0, column=3, padx=(0, 4))

        self._frame_factura = ctk.CTkScrollableFrame(col_derecha)
        self._frame_factura.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 4))

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
        frame_total.grid(row=2, column=0, sticky="ew", padx=8, pady=(2, 2))

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
        frame_botones.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 10))
        frame_botones.grid_columnconfigure(0, weight=1)
        frame_botones.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            frame_botones,
            text="Imprimir",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=44,
            command=self.imprimir_factura,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        ctk.CTkButton(
            frame_botones,
            text="Eliminar",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=44,
            fg_color="#C0392B",
            hover_color="#922B21",
            command=self._limpiar_factura,
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

        # ── Detalle de la factura ───────────────────────────────────
        frame_detalle = ctk.CTkFrame(col_derecha, fg_color="transparent")
        frame_detalle.grid(row=4, column=0, sticky="ew", padx=8, pady=(0, 8))

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
        cols = max(1, canvas_width // (self._card_width + self._card_gap))
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
            self._frame_catalogo.grid_columnconfigure(c, weight=1, minsize=self._card_width)

        for idx, producto in enumerate(productos):
            self._crear_tarjeta_producto(producto, row=idx // cols, col=idx % cols)

    def _crear_tarjeta_producto(self, producto: Producto, *, row: int, col: int) -> None:
        """Crea una tarjeta de producto cuadrada en la posición (row, col) del grid."""
        font_size = max(9, round(12 * self._card_width / 150))
        tarjeta = ctk.CTkFrame(
            self._frame_catalogo,
            width=self._card_width,
            height=self._card_height,
            corner_radius=8,
            border_width=2,
            border_color='#555555'
        )
        tarjeta.grid(
            row=row, column=col,
            padx=self._card_gap // 2, pady=self._card_gap // 2,
            sticky="n",
        )
        tarjeta.grid_propagate(False)

        tarjeta.grid_rowconfigure(0, weight=1)   # área del nombre+id: crece
        tarjeta.grid_rowconfigure(1, weight=0)   # botón: altura fija
        tarjeta.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tarjeta,
            text=f"#{producto.id} - {producto.nombre}",
            font=ctk.CTkFont(size=font_size, weight="bold"),
            text_color="white",
            wraplength=self._card_width - 16,
            anchor="center",
            justify="center",
        ).grid(row=0, column=0, padx=8, pady=(10, 4), sticky="nsew")

        ctk.CTkButton(
            tarjeta,
            text="Agregar",
            width=self._card_width - 24,
            height=30,
            font=ctk.CTkFont(size=font_size),
            command=lambda p=producto: self._agregar_a_factura(p),
        ).grid(row=1, column=0, padx=12, pady=(0, 10))

    def _buscar_producto(self) -> None:
        """Filtra el catálogo por nombre o por id (soporta prefijo #)."""
        termino = self._campo_busqueda.get().strip().lower()
        if termino:
            id_termino = termino.lstrip("#").strip()
            filtrados = [
                p for p in self._todos_productos
                if termino in p.nombre.lower() or id_termino in str(p.id)
            ]
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

            fs = self._item_font_size
            item_frame = ctk.CTkFrame(
                self._frame_factura,
                height=self._item_height,
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
            item_frame.grid_columnconfigure(4, weight=0)  # Botón ×

            lbl_cantidad = ctk.CTkLabel(
                item_frame,
                text="1",
                font=ctk.CTkFont(size=fs, weight="bold"),
                width=int(40 * fs / 14),
            )
            lbl_cantidad.grid(row=0, column=0, padx=(8, 0), pady=4, sticky="w")

            ctk.CTkButton(
                item_frame,
                text="+",
                width=int(24 * fs / 14),
                height=int(24 * fs / 14),
                font=ctk.CTkFont(size=max(10, fs - 2), weight="bold"),
                fg_color="transparent",
                border_width=1,
                command=lambda p=pid: self._abrir_popup_cantidad(p),
            ).grid(row=0, column=1, padx=4, pady=4)

            ctk.CTkLabel(
                item_frame,
                text=producto.nombre,
                font=ctk.CTkFont(size=fs),
                anchor="w",
            ).grid(row=0, column=2, padx=4, pady=4, sticky="ew")

            lbl_precio = ctk.CTkLabel(
                item_frame,
                text=f"${producto.precio:,.0f}",
                font=ctk.CTkFont(size=fs, weight="bold"),
                width=int(80 * fs / 14),
                anchor="e",
            )
            lbl_precio.grid(row=0, column=3, padx=8, pady=4, sticky="e")

            ctk.CTkButton(
                item_frame,
                text="×",
                width=int(24 * fs / 14),
                height=int(24 * fs / 14),
                font=ctk.CTkFont(size=max(10, fs - 2), weight="bold"),
                fg_color="#C0392B",
                hover_color="#922B21",
                command=lambda p=pid: self._eliminar_item(p),
            ).grid(row=0, column=4, padx=(4, 8), pady=4)

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

    def _eliminar_item(self, pid: int) -> None:
        """Elimina un ítem de la factura y actualiza el total."""
        item = self._items.pop(pid)
        self._total -= item["precio_unitario"] * item["cantidad"]
        item["label"].destroy()

        if not self._items:
            self._total = 0.0
            self._label_total.configure(text="$0")
            self._placeholder_factura = ctk.CTkLabel(
                self._frame_factura,
                text="Sin productos aún",
                text_color="gray",
                font=ctk.CTkFont(size=13),
            )
            self._placeholder_factura.pack(pady=24)
        else:
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
        """Guarda la factura en la BD, la imprime y limpia el formulario."""
        if not self._items:
            self._label_total.configure(text="Sin ítems", text_color="#FF5555")
            self.after(1500, lambda: self._label_total.configure(text="$0", text_color="#2ECC71"))
            return

        usuario = Session().usuario_actual
        detalle = self._entry_detalle.get().strip() or None
        items_snapshot = dict(self._items)  # captura antes de limpiar

        try:
            factura = factura_repo.crear(
                total=self._total, usuario_id=usuario.id, detalle=detalle
            )
            factura_item_repo.crear_items(factura.id, items_snapshot)
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

        try:
            config = configuracion_repo.get_all()
            impresora.imprimir_recibo(
                factura=factura,
                items=items_snapshot,
                config=config,
                nombre_cajera=usuario.nombre,
                detalle=detalle,
            )
            self._label_total.configure(text="Impresa ✓", text_color="#2ECC71")
            self._preguntar_copia(factura, items_snapshot, config, usuario.nombre, detalle)
        except Exception as exc:
            self._label_total.configure(text="Guardada (sin imprimir)", text_color="#F39C12")
            self._mostrar_error_impresion(str(exc))

        self.after(2500, lambda: self._label_total.configure(text="$0", text_color="#2ECC71"))

    def _preguntar_copia(
        self,
        factura: object,
        items: dict,
        config: dict,
        nombre_cajera: str,
        detalle: str | None,
    ) -> None:
        """Muestra un popup preguntando si se desea imprimir una copia."""
        raiz = self.winfo_toplevel()
        popup = ctk.CTkToplevel(raiz)
        popup.title("Imprimir copia")
        popup.resizable(False, False)
        popup.transient(raiz)

        ancho, alto = 320, 150
        raiz.update_idletasks()
        x = raiz.winfo_x() + (raiz.winfo_width() - ancho) // 2
        y = raiz.winfo_y() + (raiz.winfo_height() - alto) // 2
        popup.geometry(f"{ancho}x{alto}+{x}+{y}")
        popup.after(50, popup.grab_set)

        ctk.CTkLabel(
            popup,
            text="¿Desea imprimir una copia?",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=(24, 16), padx=16)

        frame_btns = ctk.CTkFrame(popup, fg_color="transparent")
        frame_btns.pack()

        def _imprimir_copia() -> None:
            popup.destroy()
            try:
                impresora.imprimir_recibo(
                    factura=factura,
                    items=items,
                    config=config,
                    nombre_cajera=nombre_cajera,
                    detalle=detalle,
                    es_copia=True,
                )
            except Exception as exc:
                self._mostrar_error_impresion(str(exc))

        ctk.CTkButton(
            frame_btns,
            text="Sí",
            width=100,
            command=_imprimir_copia,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            frame_btns,
            text="No",
            width=100,
            fg_color="transparent",
            border_width=1,
            command=popup.destroy,
        ).pack(side="left")

        popup.bind("<Return>", lambda _e: _imprimir_copia())
        popup.bind("<Escape>", lambda _e: popup.destroy())

    def _mostrar_error_impresion(self, mensaje: str) -> None:
        """Muestra un popup con el error de impresión."""
        raiz = self.winfo_toplevel()
        popup = ctk.CTkToplevel(raiz)
        popup.title("Error de impresión")
        popup.resizable(False, False)
        popup.transient(raiz)

        ancho, alto = 420, 200
        raiz.update_idletasks()
        x = raiz.winfo_x() + (raiz.winfo_width() - ancho) // 2
        y = raiz.winfo_y() + (raiz.winfo_height() - alto) // 2
        popup.geometry(f"{ancho}x{alto}+{x}+{y}")
        popup.after(50, popup.grab_set)

        ctk.CTkLabel(
            popup,
            text="La factura fue guardada pero no se pudo imprimir:",
            font=ctk.CTkFont(size=13, weight="bold"),
            wraplength=380,
        ).pack(pady=(18, 6), padx=16)

        ctk.CTkLabel(
            popup,
            text=mensaje,
            font=ctk.CTkFont(size=12),
            text_color="#FF5555",
            wraplength=380,
        ).pack(pady=(0, 12), padx=16)

        ctk.CTkButton(popup, text="Cerrar", width=100, command=popup.destroy).pack(pady=(0, 16))
        popup.bind("<Return>", lambda _e: popup.destroy())

    # ── Resize del catálogo ─────────────────────────────────────────────────────

    def _aumentar_catalogo(self) -> None:
        if self._card_width >= 400:
            return
        self._card_width = min(400, self._card_width + 20)
        self._card_height = round(self._card_width * 100 / 150)
        self._num_columnas = 0  # fuerza re-render en _reflow_grid
        w = self._frame_catalogo._parent_canvas.winfo_width()
        self._reflow_grid(w if w > 1 else 600)

    def _reducir_catalogo(self) -> None:
        if self._card_width <= 80:
            return
        self._card_width = max(80, self._card_width - 20)
        self._card_height = round(self._card_width * 100 / 150)
        self._num_columnas = 0
        w = self._frame_catalogo._parent_canvas.winfo_width()
        self._reflow_grid(w if w > 1 else 600)

    # ── Resize de la factura ────────────────────────────────────────────────────

    def _aumentar_factura(self) -> None:
        if self._item_font_size >= 36:
            return
        self._item_font_size = min(36, self._item_font_size + 2)
        self._item_height = round(50 * self._item_font_size / 14)
        self._reconstruir_items_factura()

    def _reducir_factura(self) -> None:
        if self._item_font_size <= 10:
            return
        self._item_font_size = max(10, self._item_font_size - 2)
        self._item_height = round(50 * self._item_font_size / 14)
        self._reconstruir_items_factura()

    def _reconstruir_items_factura(self) -> None:
        """Destruye y recrea los ítems de la factura con el tamaño actual."""
        for widget in self._frame_factura.winfo_children():
            widget.destroy()

        if not self._items:
            self._placeholder_factura = ctk.CTkLabel(
                self._frame_factura,
                text="Sin productos aún",
                text_color="gray",
                font=ctk.CTkFont(size=13),
            )
            self._placeholder_factura.pack(pady=24)
            return

        fs = self._item_font_size
        ih = self._item_height

        for pid, item in self._items.items():
            item_frame = ctk.CTkFrame(
                self._frame_factura,
                height=ih,
                border_width=1,
                border_color="#555555",
                corner_radius=6,
            )
            item_frame.pack(fill="x", padx=8, pady=4)
            item_frame.pack_propagate(False)

            item_frame.grid_columnconfigure(0, weight=0)
            item_frame.grid_columnconfigure(1, weight=0)
            item_frame.grid_columnconfigure(2, weight=1)
            item_frame.grid_columnconfigure(3, weight=0)
            item_frame.grid_columnconfigure(4, weight=0)  # Botón ×

            lbl_cantidad = ctk.CTkLabel(
                item_frame,
                text=f"{item['cantidad']:g}",
                font=ctk.CTkFont(size=fs, weight="bold"),
                width=int(40 * fs / 14),
            )
            lbl_cantidad.grid(row=0, column=0, padx=(8, 0), pady=4, sticky="w")

            ctk.CTkButton(
                item_frame,
                text="+",
                width=int(24 * fs / 14),
                height=int(24 * fs / 14),
                font=ctk.CTkFont(size=max(10, fs - 2), weight="bold"),
                fg_color="transparent",
                border_width=1,
                command=lambda p=pid: self._abrir_popup_cantidad(p),
            ).grid(row=0, column=1, padx=4, pady=4)

            ctk.CTkLabel(
                item_frame,
                text=item["nombre"],
                font=ctk.CTkFont(size=fs),
                anchor="w",
            ).grid(row=0, column=2, padx=4, pady=4, sticky="ew")

            lbl_precio = ctk.CTkLabel(
                item_frame,
                text=f"${item['precio_unitario'] * item['cantidad']:,.0f}",
                font=ctk.CTkFont(size=fs, weight="bold"),
                width=int(80 * fs / 14),
                anchor="e",
            )
            lbl_precio.grid(row=0, column=3, padx=8, pady=4, sticky="e")

            ctk.CTkButton(
                item_frame,
                text="×",
                width=int(24 * fs / 14),
                height=int(24 * fs / 14),
                font=ctk.CTkFont(size=max(10, fs - 2), weight="bold"),
                fg_color="#C0392B",
                hover_color="#922B21",
                command=lambda p=pid: self._eliminar_item(p),
            ).grid(row=0, column=4, padx=(4, 8), pady=4)

            item["label"] = item_frame
            item["lbl_cantidad"] = lbl_cantidad
            item["lbl_precio"] = lbl_precio

    def _volver_a_home(self) -> None:
        """Regresa a la pantalla principal."""
        self._navigate("home")
