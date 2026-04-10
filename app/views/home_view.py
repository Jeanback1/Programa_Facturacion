# -*- coding: utf-8 -*-
"""Vista principal post-login."""

import customtkinter as ctk

from app.session import Session


class HomeView(ctk.CTk):
    """Pantalla principal de la aplicación, visible tras autenticarse."""

    def __init__(self) -> None:
        super().__init__()

        session = Session()
        self.title(f"Facturación — {session.usuario_actual.nombre}")
        self.geometry("860x560")
        self.minsize(640, 420)

        # Interceptar el cierre de ventana para limpiar la sesión
        self.protocol("WM_DELETE_WINDOW", self.destroy)

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
            command=self._cerrar_sesion,
        ).pack(side="right", padx=20, pady=15)

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
            command=lambda: self._navegar("Facturar"),
            **btn_kwargs,
        ).grid(row=0, column=0, padx=18, pady=10)

        ctk.CTkButton(
            botones_frame,
            text="Cuadre",
            command=lambda: self._navegar("Cuadre"),
            **btn_kwargs,
        ).grid(row=0, column=1, padx=18, pady=10)

        # El botón de Gestión solo se agrega si el usuario es administrador
        if session.es_admin():
            ctk.CTkButton(
                botones_frame,
                text="Gestión",
                command=lambda: self._navegar("Gestión"),
                **btn_kwargs,
            ).grid(row=0, column=2, padx=18, pady=10)

    # ── Acciones ───────────────────────────────────────────────────────────────

    def _navegar(self, destino: str) -> None:
        """Placeholder para la navegación a módulos futuros."""
        print(f"Navegar a: {destino}")

    def _cerrar_sesion(self) -> None:
        """Limpia la sesión activa y regresa a la pantalla de login."""
        Session().cerrar_sesion()
        self._abrir_login()

    def _abrir_login(self) -> None:
        """Destruye esta ventana y abre la pantalla de login."""
        # Importación diferida para evitar ciclo de importaciones
        from app.views.login_view import LoginView

        self.destroy()
        app = LoginView()
        app.mainloop()
