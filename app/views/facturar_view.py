# -*- coding: utf-8 -*-
"""Vista de facturación — catálogo de productos y lista de la factura actual."""

from collections.abc import Callable

import customtkinter as ctk


class FacturarView(ctk.CTkFrame):
    """Frame de facturación con catálogo de productos y lista de la factura actual."""

    def __init__(self, master: ctk.CTk, navigate: Callable[[str], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self._navigate = navigate

        master.title("Facturación — Facturar")
        master.geometry("1100x680")
        master.minsize(800, 500)
        master.resizable(True, True)

        self._construir_ui()

    def _construir_ui(self) -> None:
        """Construye todos los widgets de la pantalla de facturación."""

        # ── Header ─────────────────────────────────────────────────
        header = ctk.CTkFrame(self, height=56, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Botón para regresar a la pantalla principal
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
        # Llamar a buscar_producto() cada vez que el usuario escribe
        self._campo_busqueda.bind("<KeyRelease>", lambda _event: self.buscar_producto())

        # ── Área de dos columnas ────────────────────────────────────
        area_columnas = ctk.CTkFrame(self, fg_color="transparent")
        area_columnas.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # Proporción 70 % izquierda / 30 % derecha
        area_columnas.grid_columnconfigure(0, weight=7)
        area_columnas.grid_columnconfigure(1, weight=3)
        area_columnas.grid_rowconfigure(0, weight=1)

        # ── Columna izquierda — Catálogo ────────────────────────────
        col_izquierda = ctk.CTkFrame(area_columnas, fg_color="transparent")
        col_izquierda.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        col_izquierda.grid_rowconfigure(0, weight=1)
        col_izquierda.grid_columnconfigure(0, weight=1)

        # Frame desplazable donde se renderizarán las tarjetas del catálogo
        self._frame_catalogo = ctk.CTkScrollableFrame(
            col_izquierda,
            label_text="Catálogo",
            label_font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._frame_catalogo.grid(row=0, column=0, sticky="nsew")

        # Placeholder hasta que se carguen los productos desde la BD
        ctk.CTkLabel(
            self._frame_catalogo,
            text="Los productos aparecerán aquí",
            text_color="gray",
            font=ctk.CTkFont(size=13),
        ).pack(pady=24)

        # ── Columna derecha — Lista de la factura ───────────────────
        col_derecha = ctk.CTkFrame(area_columnas)
        col_derecha.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        col_derecha.grid_rowconfigure(0, weight=1)
        col_derecha.grid_columnconfigure(0, weight=1)

        # Frame desplazable con los productos ya agregados a la factura
        self._frame_factura = ctk.CTkScrollableFrame(
            col_derecha,
            label_text="Factura actual",
            label_font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._frame_factura.grid(row=0, column=0, sticky="nsew", padx=8, pady=(8, 4))

        # Placeholder hasta que el usuario agregue productos
        ctk.CTkLabel(
            self._frame_factura,
            text="Lista de productos agregados",
            text_color="gray",
            font=ctk.CTkFont(size=13),
        ).pack(pady=24)

        # ── Botones inferiores (fuera del scroll) ───────────────────
        frame_botones = ctk.CTkFrame(col_derecha, fg_color="transparent")
        frame_botones.grid(row=1, column=0, sticky="ew", padx=8, pady=(4, 10))
        frame_botones.grid_columnconfigure(0, weight=1)
        frame_botones.grid_columnconfigure(1, weight=1)

        # Botón para imprimir la factura actual
        ctk.CTkButton(
            frame_botones,
            text="Imprimir",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.imprimir_factura,
        ).grid(row=0, column=0, sticky="ew", padx=(0, 4))

        # Botón para eliminar el producto seleccionado de la factura
        ctk.CTkButton(
            frame_botones,
            text="Eliminar",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#C0392B",
            hover_color="#922B21",
            command=self.eliminar_producto,
        ).grid(row=0, column=1, sticky="ew", padx=(4, 0))

    # ── Acciones (placeholders — lógica de BD en siguiente fase) ───────────────

    def buscar_producto(self) -> None:
        """Filtra el catálogo según el texto ingresado en la barra de búsqueda."""
        print("buscar_producto()")

    def agregar_producto(self) -> None:
        """Agrega el producto seleccionado a la lista de la factura actual."""
        print("agregar_producto()")

    def imprimir_factura(self) -> None:
        """Envía la factura actual a impresión."""
        print("imprimir_factura()")

    def eliminar_producto(self) -> None:
        """Elimina el producto seleccionado de la lista de la factura."""
        print("eliminar_producto()")

    def _volver_a_home(self) -> None:
        """Regresa a la pantalla principal."""
        self._navigate("home")
