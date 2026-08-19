# -*- coding: utf-8 -*-
"""Vista de gestión de productos — solo accesible para administradores."""

from collections.abc import Callable

import customtkinter as ctk

from app.repositories import producto_repo
from app.theme import ThemeManager


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
            text_color=ThemeManager().color("transparent_btn_text"),
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
        col_form = ctk.CTkScrollableFrame(contenido)
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

        # ── Variantes opcionales ────────────────────────────────────
        self._frame_variantes = ctk.CTkFrame(col_form, fg_color="transparent")
        self._frame_variantes.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            self._frame_variantes,
            text="Variantes (opcional)",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            self._frame_variantes,
            text="Si agrega variantes (ej. Para llevar / Para comer aquí),\ncada una con su propio precio, al facturar se preguntará cuál elegir.\nDeje vacío para un producto normal.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            justify="left",
        ).pack(anchor="w", pady=(0, 6))

        self._filas_variantes: list[tuple[ctk.CTkEntry, ctk.CTkEntry]] = []

        ctk.CTkButton(
            self._frame_variantes,
            text="+ Agregar variante",
            height=28,
            fg_color="transparent",
            border_width=1,
            text_color=ThemeManager().color("transparent_btn_text"),
            font=ctk.CTkFont(size=12),
            command=self._agregar_fila_variante,
        ).pack(anchor="w", pady=(0, 6))

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
        """Valida el formulario, inserta el producto (y variantes) y refresca la lista."""
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

        variantes = self._recoger_variantes()
        if variantes is None:
            self._mostrar_mensaje("Revise las variantes: complete nombre y precio en cada una.", error=True)
            return

        producto_repo.crear(nombre, precio, variantes)
        self._campo_nombre.delete(0, "end")
        self._campo_precio.delete(0, "end")
        self._limpiar_variantes()
        self._campo_nombre.focus()
        self._mostrar_mensaje(f'"{nombre}" agregado correctamente.', error=False)
        self._cargar_lista()

    # ── Variantes del formulario ──────────────────────────────────────────

    def _agregar_fila_variante(self) -> None:
        """Añade una fila editable (nombre + precio) para una variante."""
        fila = ctk.CTkFrame(self._frame_variantes, fg_color="transparent")
        fila.pack(fill="x", pady=2)
        fila.grid_columnconfigure(0, weight=2)
        fila.grid_columnconfigure(1, weight=1)
        fila.grid_columnconfigure(2, weight=0)

        entry_nombre = ctk.CTkEntry(fila, placeholder_text="Nombre variante")
        entry_nombre.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        entry_precio = ctk.CTkEntry(fila, placeholder_text="Precio")
        entry_precio.grid(row=0, column=1, sticky="ew", padx=(0, 4))

        def _quitar() -> None:
            fila.destroy()
            if (entry_nombre, entry_precio) in self._filas_variantes:
                self._filas_variantes.remove((entry_nombre, entry_precio))

        ctk.CTkButton(
            fila,
            text="✕",
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=ThemeManager().color("danger_hover"),
            text_color=ThemeManager().color("danger_bg"),
            font=ctk.CTkFont(size=12, weight="bold"),
            command=_quitar,
        ).grid(row=0, column=2)

        self._filas_variantes.append((entry_nombre, entry_precio))

    def _recoger_variantes(self) -> list[tuple[str, float]] | None:
        """Lee las filas de variantes. Devuelve la lista o None si hay alguna incompleta/inválida."""
        variantes: list[tuple[str, float]] = []
        for entry_nombre, entry_precio in self._filas_variantes:
            nombre = entry_nombre.get().strip()
            precio_str = entry_precio.get().strip()
            # Fila totalmente vacía = se ignora
            if not nombre and not precio_str:
                continue
            if not nombre:
                return None
            try:
                precio = float(precio_str.replace(",", "."))
                if precio < 0:
                    raise ValueError
            except ValueError:
                return None
            variantes.append((nombre, precio))
        return variantes

    def _limpiar_variantes(self) -> None:
        """Elimina todas las filas de variantes del formulario."""
        for fila in list(self._frame_variantes.winfo_children()):
            # Solo destruye los frames de filas creados; no el label ni el botón.
            # Las filas se guardan en _filas_variantes y son CTkFrame.
            if isinstance(fila, ctk.CTkFrame):
                fila.destroy()
        self._filas_variantes.clear()

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
                font=ctk.CTkFont(size=13, weight="bold" if p.variantes else "normal"),
            ).grid(row=0, column=0, sticky="w", padx=8)

            ctk.CTkLabel(
                fila,
                text=f"${p.precio:,.0f}",
                anchor="e",
                text_color="gray",
                font=ctk.CTkFont(size=13),
            ).grid(row=0, column=1, sticky="e", padx=8)

            ctk.CTkButton(
                fila,
                text="Eliminar",
                width=80,
                height=26,
                fg_color="transparent",
                border_width=1,
                text_color=ThemeManager().color("error_text"),
                hover_color=ThemeManager().color("danger_hover"),
                font=ctk.CTkFont(size=12),
                command=lambda prod=p: self._confirmar_eliminar(prod),
            ).grid(row=0, column=2, sticky="e", padx=(4, 8))

            # Sub-líneas con las variantes del producto
            for i, v in enumerate(p.variantes):
                ctk.CTkLabel(
                    fila,
                    text=f"    · {v.nombre}: ${v.precio:,.0f}",
                    anchor="w",
                    text_color="gray",
                    font=ctk.CTkFont(size=12),
                ).grid(row=i + 1, column=0, sticky="w", columnspan=2, padx=8)

    def _confirmar_eliminar(self, producto) -> None:
        """Abre un diálogo modal de confirmación antes de eliminar el producto."""
        raiz = self.winfo_toplevel()
        dialogo = ctk.CTkToplevel(raiz)
        dialogo.title("Confirmar eliminación")
        dialogo.resizable(False, False)
        dialogo.transient(raiz)

        ancho, alto = 360, 170
        raiz.update_idletasks()
        x = raiz.winfo_x() + (raiz.winfo_width() - ancho) // 2
        y = raiz.winfo_y() + (raiz.winfo_height() - alto) // 2
        dialogo.geometry(f"{ancho}x{alto}+{x}+{y}")
        dialogo.after(50, dialogo.grab_set)

        ctk.CTkLabel(
            dialogo,
            text=f'¿Eliminar "{producto.nombre}"?',
            font=ctk.CTkFont(size=14),
            justify="center",
        ).pack(pady=(28, 20))

        frame_btns = ctk.CTkFrame(dialogo, fg_color="transparent")
        frame_btns.pack()

        ctk.CTkButton(
            frame_btns,
            text="Cancelar",
            width=120,
            fg_color="transparent",
            border_width=1,
            text_color=ThemeManager().color("transparent_btn_text"),
            command=dialogo.destroy,
        ).pack(side="left", padx=10)

        def _eliminar() -> None:
            producto_repo.eliminar(producto.id)
            dialogo.destroy()
            self._cargar_lista()

        ctk.CTkButton(
            frame_btns,
            text="Eliminar",
            width=120,
            fg_color=ThemeManager().color("danger_bg"),
            hover_color=ThemeManager().color("danger_hover"),
            command=_eliminar,
        ).pack(side="left", padx=10)

    def _mostrar_mensaje(self, texto: str, *, error: bool) -> None:
        _c = ThemeManager().color
        color = _c("error_text") if error else _c("success")
        self._label_mensaje.configure(text=texto, text_color=color)

    def _volver_a_home(self) -> None:
        self._navigate("home")
