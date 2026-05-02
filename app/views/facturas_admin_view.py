# -*- coding: utf-8 -*-
"""Vista de administración de facturas — solo accesible para el rol admin."""

from collections.abc import Callable

import customtkinter as ctk

from app.models.factura import Factura
from app.repositories import factura_repo, usuario_repo
from app.theme import ThemeManager


class FacturasAdminView(ctk.CTkFrame):
    """Frame que lista todas las facturas de todos los usuarios y permite borrarlas."""

    def __init__(self, master: ctk.CTk, navigate: Callable[[str], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self._navigate = navigate

        master.title("Facturación — Historial de Facturas")
        master.geometry("1100x680")
        master.minsize(900, 500)
        master.resizable(True, True)

        self._facturas: list[Factura] = []
        self._usuarios: dict[int, str] = {}

        self._construir_ui()
        self._cargar_datos()

    def _construir_ui(self) -> None:
        # ── Header ──────────────────────────────────────────────────
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
            command=lambda: self._navigate("home"),
        ).pack(side="left", padx=16, pady=10)

        ctk.CTkLabel(
            header,
            text="Historial de Facturas",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=8, pady=10)

        # ── Body ────────────────────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)

        self._lista = ctk.CTkScrollableFrame(
            body,
            label_text="Todas las facturas",
            label_font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._lista.grid(row=0, column=0, sticky="nsew")

    # ── Datos ────────────────────────────────────────────────────────────────────

    def _cargar_datos(self) -> None:
        self._facturas = factura_repo.listar_todos()
        self._usuarios = {u.id: u.nombre for u in usuario_repo.listar_todos()}
        self._renderizar()

    # ── Renderizado ──────────────────────────────────────────────────────────────

    def _renderizar(self) -> None:
        for widget in self._lista.winfo_children():
            widget.destroy()

        if not self._facturas:
            ctk.CTkLabel(
                self._lista,
                text="No hay facturas registradas",
                text_color="gray",
                font=ctk.CTkFont(size=13),
            ).pack(pady=24)
            return

        for factura in self._facturas:
            self._crear_fila(factura)

    def _crear_fila(self, factura: Factura) -> None:
        tm = ThemeManager()
        fila = ctk.CTkFrame(
            self._lista,
            height=44,
            border_width=1,
            border_color=tm.color("border"),
            corner_radius=6,
        )
        fila.pack(fill="x", padx=8, pady=3)
        fila.pack_propagate(False)
        fila.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            fila,
            text=f"#{factura.id}",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=50,
            anchor="center",
        ).grid(row=0, column=0, padx=(8, 4), pady=4)

        nombre_usuario = self._usuarios.get(factura.usuario_id, f"#{factura.usuario_id}")
        ctk.CTkLabel(
            fila,
            text=nombre_usuario,
            font=ctk.CTkFont(size=12),
            width=130,
            anchor="w",
        ).grid(row=0, column=1, padx=4, pady=4)

        ctk.CTkLabel(
            fila,
            text=factura.hora_facturacion[:16],
            font=ctk.CTkFont(size=12),
            width=120,
            anchor="w",
        ).grid(row=0, column=2, padx=4, pady=4)

        ctk.CTkLabel(
            fila,
            text=f"${factura.total:,.0f}",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=90,
            anchor="e",
        ).grid(row=0, column=3, padx=4, pady=4, sticky="e")

        estado = "Cuadrada" if factura.cuadre_id is not None else "Pendiente"
        estado_color = "gray" if factura.cuadre_id is not None else tm.color("transparent_btn_text")
        ctk.CTkLabel(
            fila,
            text=estado,
            font=ctk.CTkFont(size=12),
            width=80,
            text_color=estado_color,
            anchor="center",
        ).grid(row=0, column=4, padx=4, pady=4)

        ctk.CTkButton(
            fila,
            text="Eliminar",
            width=80,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color=tm.color("danger_bg"),
            hover_color=tm.color("danger_hover"),
            command=lambda f=factura: self._confirmar_eliminacion(f),
        ).grid(row=0, column=5, padx=(4, 8), pady=4)

    # ── Acciones ─────────────────────────────────────────────────────────────────

    def _confirmar_eliminacion(self, factura: Factura) -> None:
        raiz = self.winfo_toplevel()
        dialogo = ctk.CTkToplevel(raiz)
        dialogo.title("Confirmar eliminación")
        dialogo.resizable(False, False)
        dialogo.transient(raiz)

        ancho, alto = 420, 200 if factura.cuadre_id is None else 240
        raiz.update_idletasks()
        x = raiz.winfo_x() + (raiz.winfo_width() - ancho) // 2
        y = raiz.winfo_y() + (raiz.winfo_height() - alto) // 2
        dialogo.geometry(f"{ancho}x{alto}+{x}+{y}")
        dialogo.after(50, dialogo.grab_set)

        nombre_usuario = self._usuarios.get(factura.usuario_id, f"#{factura.usuario_id}")
        ctk.CTkLabel(
            dialogo,
            text=f"¿Eliminar Factura #{factura.id}?",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(pady=(20, 6))

        ctk.CTkLabel(
            dialogo,
            text=f"{nombre_usuario}  ·  {factura.hora_facturacion[:16]}  ·  ${factura.total:,.0f}",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(pady=(0, 6))

        if factura.cuadre_id is not None:
            ctk.CTkLabel(
                dialogo,
                text="⚠ Esta factura ya pertenece a un cuadre.\nEliminarla afectará el historial de cuadres.",
                font=ctk.CTkFont(size=12),
                text_color="orange",
                justify="center",
            ).pack(pady=(0, 10))

        botones = ctk.CTkFrame(dialogo, fg_color="transparent")
        botones.pack(pady=(0, 20))

        ctk.CTkButton(
            botones,
            text="Cancelar",
            width=110,
            fg_color="transparent",
            border_width=1,
            text_color=ThemeManager().color("transparent_btn_text"),
            command=dialogo.destroy,
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            botones,
            text="Sí, eliminar",
            width=110,
            fg_color=ThemeManager().color("danger_bg"),
            hover_color=ThemeManager().color("danger_hover"),
            command=lambda: self._ejecutar_eliminacion(factura, dialogo),
        ).pack(side="left", padx=8)

    def _ejecutar_eliminacion(self, factura: Factura, dialogo: ctk.CTkToplevel) -> None:
        dialogo.destroy()
        try:
            factura_repo.eliminar(factura.id)
        except RuntimeError as e:
            from tkinter import messagebox
            messagebox.showerror("Error", str(e))
            return
        self._cargar_datos()
