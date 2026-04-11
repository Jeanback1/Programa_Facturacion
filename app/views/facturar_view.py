# -*- coding: utf-8 -*-
"""Vista de facturación — catálogo de productos y lista de la factura actual."""

from collections.abc import Callable

import customtkinter as ctk

from app.models.producto import Producto
from app.repositories import producto_repo

_CARD_WIDTH: int = 150
_CARD_HEIGHT: int = 165
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
            item_frame = item["label"]
            
            # Obtener referencias confiables a los labels
            cantidad_label = item_frame.winfo_children()[0]
            nombre_label = item_frame.winfo_children()[1]
            precio_label = item_frame.winfo_children()[2]
            
            # Actualizar cantidad y precio manteniendo el nombre
            cantidad_label.configure(text=f"{item['cantidad']}")
            total = item["precio_unitario"] * item["cantidad"]
            precio_label.configure(text=f"${total:,.0f}")
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
            
            # Configurar grid layout dentro del frame
            item_frame.grid_columnconfigure(0, weight=0)  # Cantidad
            item_frame.grid_columnconfigure(1, weight=1)  # Nombre
            item_frame.grid_columnconfigure(2, weight=0)  # Precio
            
            # Cantidad
            ctk.CTkLabel(
                item_frame,
                text=f"{1}",
                font=ctk.CTkFont(size=14, weight="bold"),
                width=40
            ).grid(row=0, column=0, padx=8, pady=4, sticky="w")
            
            # Nombre
            ctk.CTkLabel(
                item_frame,
                text=producto.nombre,
                font=ctk.CTkFont(size=14),
                anchor="w"
            ).grid(row=0, column=1, padx=4, pady=4, sticky="ew")
            
            # Precio total
            total = producto.precio * 1
            ctk.CTkLabel(
                item_frame,
                text=f"${total:,.0f}",
                font=ctk.CTkFont(size=14, weight="bold"),
                width=80,
                anchor="e"
            ).grid(row=0, column=2, padx=8, pady=4, sticky="e")

            self._items[pid] = {
                "nombre": producto.nombre,
                "precio_unitario": producto.precio,
                "cantidad": 1,
                "label": item_frame,
            }

        self._total += producto.precio
        self._label_total.configure(text=f"${self._total:,.0f}")

    def _limpiar_factura(self) -> None:
        """Elimina todos los productos de la factura y resetea el total."""
        for widget in self._frame_factura.winfo_children():
            widget.destroy()

        self._items.clear()
        self._total = 0.0
        self._label_total.configure(text="$0")

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
        """Envía la factura actual a impresión (placeholder)."""
        print("imprimir_factura()")

    def _volver_a_home(self) -> None:
        """Regresa a la pantalla principal."""
        self._navigate("home")
