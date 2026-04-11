# -*- coding: utf-8 -*-
"""Vista de gestión de productos — solo accesible para administradores."""

from collections.abc import Callable

import customtkinter as ctk

from app.repositories import producto_repo


class GestionView(ctk.CTkFrame):
    """Frame de gestión: alta de productos y listado del catálogo."""

    def __init__(self, master: ctk.CTk, navigate: Callable[[str], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self._navigate = navigate

        master.title("Facturación — Gestión de Productos")
        master.geometry("800x600")
        master.minsize(600, 450)
        master.resizable(True, True)

        self._construir_ui()

    def _construir_ui(self) -> None:
        """Construye todos los widgets de la pantalla de gestión."""

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

        ctk.CTkLabel(
            header,
            text="Gestión de Productos",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=8, pady=10)

        # ── Área de dos columnas ────────────────────────────────────
        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.pack(fill="both", expand=True, padx=16, pady=12)
        contenido.grid_columnconfigure(0, weight=1)
        contenido.grid_columnconfigure(1, weight=2)
        contenido.grid_rowconfigure(0, weight=1)

        # ── Columna izquierda — formulario ──────────────────────────
        col_form = ctk.CTkFrame(contenido)
        col_form.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            col_form,
            text="Nuevo producto",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(padx=20, pady=(20, 16))

        ctk.CTkLabel(col_form, text="Nombre", anchor="w").pack(fill="x", padx=20)
        self._campo_nombre = ctk.CTkEntry(
            col_form, placeholder_text="Ej. Arroz 500g"
        )
        self._campo_nombre.pack(fill="x", padx=20, pady=(4, 14))

        ctk.CTkLabel(col_form, text="Precio", anchor="w").pack(fill="x", padx=20)
        self._campo_precio = ctk.CTkEntry(
            col_form, placeholder_text="Ej. 1500"
        )
        self._campo_precio.pack(fill="x", padx=20, pady=(4, 18))

        ctk.CTkButton(
            col_form,
            text="Agregar producto",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._agregar_producto,
        ).pack(fill="x", padx=20)

        self._label_mensaje = ctk.CTkLabel(
            col_form,
            text="",
            wraplength=200,
            font=ctk.CTkFont(size=12),
        )
        self._label_mensaje.pack(padx=20, pady=(10, 4))

        # ── Columna derecha — lista de productos ────────────────────
        col_lista = ctk.CTkFrame(contenido, fg_color="transparent")
        col_lista.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        col_lista.grid_rowconfigure(0, weight=1)
        col_lista.grid_columnconfigure(0, weight=1)

        self._frame_lista = ctk.CTkScrollableFrame(
            col_lista,
            label_text="Productos registrados",
            label_font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._frame_lista.grid(row=0, column=0, sticky="nsew")
        self._frame_lista.grid_columnconfigure(0, weight=1)

        self._cargar_lista()

    def _agregar_producto(self) -> None:
        """Valida el formulario, inserta el producto y refresca la lista."""
        nombre = self._campo_nombre.get().strip()
        precio_str = self._campo_precio.get().strip().replace(",", ".")

        if not nombre:
            self._mostrar_mensaje("El nombre no puede estar vacío.", error=True)
            return

        try:
            precio = float(precio_str)
            if precio < 0:
                raise ValueError
        except ValueError:
            self._mostrar_mensaje("Ingrese un precio válido (número positivo).", error=True)
            return

        producto_repo.crear(nombre, precio)
        self._campo_nombre.delete(0, "end")
        self._campo_precio.delete(0, "end")
        self._campo_nombre.focus()
        self._mostrar_mensaje(f'"{nombre}" agregado correctamente.', error=False)
        self._cargar_lista()

    def _cargar_lista(self) -> None:
        """Destruye y re-renderiza la lista de productos desde la BD."""
        for widget in self._frame_lista.winfo_children():
            widget.destroy()

        productos = producto_repo.listar_todos()

        if not productos:
            ctk.CTkLabel(
                self._frame_lista,
                text="No hay productos registrados",
                text_color="gray",
            ).pack(pady=20)
            return

        for p in productos:
            fila = ctk.CTkFrame(self._frame_lista, fg_color="transparent")
            fila.pack(fill="x", padx=4, pady=2)
            fila.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                fila,
                text=p.nombre,
                anchor="w",
                font=ctk.CTkFont(size=13),
            ).grid(row=0, column=0, sticky="w", padx=8)

            ctk.CTkLabel(
                fila,
                text=f"${p.precio:,.0f}",
                anchor="e",
                text_color="gray",
                font=ctk.CTkFont(size=13),
            ).grid(row=0, column=1, sticky="e", padx=8)

    def _mostrar_mensaje(self, texto: str, *, error: bool) -> None:
        color = "#FF5555" if error else "#2ECC71"
        self._label_mensaje.configure(text=texto, text_color=color)

    def _volver_a_home(self) -> None:
        self._navigate("home")
