# -*- coding: utf-8 -*-
"""Vista principal post-login."""

from collections.abc import Callable

import customtkinter as ctk

from app.session import Session
from app.theme import ThemeManager


class HomeView(ctk.CTkFrame):
    """Frame principal de la aplicación, visible tras autenticarse."""

    def __init__(self, master: ctk.CTk, navigate: Callable[[str], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self._navigate = navigate

        session = Session()
        master.title(f"Facturación — {session.usuario_actual.nombre}")
        master.geometry("860x560")
        master.minsize(640, 420)
        master.resizable(True, True)
        master.protocol("WM_DELETE_WINDOW", master.destroy)

        self._construir_ui()

    def _construir_ui(self) -> None:
        """Construye todos los widgets de la pantalla principal."""
        session = Session()
        usuario = session.usuario_actual

        # ── Header ─────────────────────────────────────────────────
        header = ctk.CTkFrame(self, height=64, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Nombre del negocio a la izquierda
        ctk.CTkLabel(
            header,
            text="Mi Negocio",
            font=ctk.CTkFont(size=22, weight="bold"),
        ).pack(side="left", padx=24, pady=14)

        # Botón cerrar sesión a la derecha
        ctk.CTkButton(
            header,
            text="Cerrar sesión",
            width=140,
            height=34,
            fg_color="transparent",
            border_width=1,
            text_color=ThemeManager().color("transparent_btn_text"),
            command=self._cerrar_sesion,
        ).pack(side="right", padx=20, pady=15)

        # Botón alternar tema (a la izquierda del botón de cerrar sesión)
        tm = ThemeManager()
        ctk.CTkButton(
            header,
            text="☀ Claro" if tm.mode == "dark" else "☾ Oscuro",
            width=120,
            height=34,
            fg_color="transparent",
            border_width=1,
            text_color=tm.color("transparent_btn_text"),
            command=self._toggle_tema,
        ).pack(side="right", padx=(0, 8), pady=15)

        # Nombre del usuario activo junto al botón
        ctk.CTkLabel(
            header,
            text=f"Hola, {usuario.nombre}",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).pack(side="right", padx=6, pady=15)

        # ── Área central ───────────────────────────────────────────
        contenido = ctk.CTkFrame(self, fg_color="transparent")
        contenido.pack(expand=True, fill="both", padx=60, pady=50)

        ctk.CTkLabel(
            contenido,
            text="¿Qué desea hacer?",
            font=ctk.CTkFont(size=20),
        ).pack(pady=(0, 36))

        # Marco de botones con grid centrado
        botones_frame = ctk.CTkFrame(contenido, fg_color="transparent")
        botones_frame.pack(expand=True)

        # Configuración común de los botones principales
        btn_kwargs = dict(width=200, height=110, font=ctk.CTkFont(size=20, weight="bold"))

        ctk.CTkButton(
            botones_frame,
            text="Facturar",
            command=lambda: self._navigate("facturar"),
            **btn_kwargs,
        ).grid(row=0, column=0, padx=18, pady=10)

        ctk.CTkButton(
            botones_frame,
            text="Cuadre",
            command=lambda: self._navigate("cuadre"),
            **btn_kwargs,
        ).grid(row=0, column=1, padx=18, pady=10)

        # Los botones de Gestión, Administrar Cuentas y Configuración solo para admin
        if session.es_admin():
            ctk.CTkButton(
                botones_frame,
                text="Gestión",
                command=lambda: self._navigate("gestion"),
                **btn_kwargs,
            ).grid(row=1, column=0, padx=18, pady=10)

            ctk.CTkButton(
                botones_frame,
                text="Administrar\nCuentas",
                command=lambda: self._navigate("cuentas"),
                **btn_kwargs,
            ).grid(row=1, column=1, padx=18, pady=10)

            ctk.CTkButton(
                botones_frame,
                text="Configuración",
                command=lambda: self._navigate("configuracion"),
                **btn_kwargs,
            ).grid(row=2, column=0, columnspan=2, padx=18, pady=10)

    # ── Acciones ───────────────────────────────────────────────────────────────

    def _toggle_tema(self) -> None:
        """Alterna entre modo claro y oscuro y recarga la vista."""
        ThemeManager().toggle()
        self._navigate("home")

    def _cerrar_sesion(self) -> None:
        """Limpia la sesión activa y regresa a la pantalla de login."""
        Session().cerrar_sesion()
        self._navigate("login")
