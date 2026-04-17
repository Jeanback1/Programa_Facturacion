# -*- coding: utf-8 -*-
"""Vista de inicio de sesión."""

from collections.abc import Callable

import bcrypt
import customtkinter as ctk

from app.repositories import usuario_repo
from app.session import Session
from app.theme import ThemeManager


class LoginView(ctk.CTkFrame):
    """Frame de login. Se monta dentro de la ventana raíz App."""

    def __init__(self, master: ctk.CTk, navigate: Callable[[str], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self._navigate = navigate

        # Configurar la ventana raíz para esta vista
        master.title("Facturación — Iniciar sesión")
        master.resizable(False, False)
        master.update_idletasks()
        ancho, alto = 420, 520
        x = (master.winfo_screenwidth() // 2) - (ancho // 2)
        y = (master.winfo_screenheight() // 2) - (alto // 2)
        master.geometry(f"{ancho}x{alto}+{x}+{y}")

        self._construir_ui()

        # Enter también dispara el intento de login
        master.bind("<Return>", lambda _event: self._intentar_login())
        self._campo_usuario.focus()

    def _construir_ui(self) -> None:
        """Construye todos los widgets de la pantalla de login."""
        # Contenedor central flotante
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.place(relx=0.5, rely=0.5, anchor="center")

        # ── Encabezado ─────────────────────────────────────────────
        ctk.CTkLabel(
            frame,
            text="Mi Negocio",
            font=ctk.CTkFont(size=30, weight="bold"),
        ).pack(pady=(0, 6))

        ctk.CTkLabel(
            frame,
            text="Sistema de Facturación",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        ).pack(pady=(0, 40))

        # ── Campo usuario ───────────────────────────────────────────
        ctk.CTkLabel(frame, text="Usuario", anchor="w", width=300).pack(pady=(0, 4))
        self._campo_usuario = ctk.CTkEntry(
            frame, width=300, placeholder_text="Ingrese su usuario"
        )
        self._campo_usuario.pack(pady=(0, 18))

        # ── Campo contraseña ────────────────────────────────────────
        ctk.CTkLabel(frame, text="Contraseña", anchor="w", width=300).pack(pady=(0, 4))
        self._campo_password = ctk.CTkEntry(
            frame, width=300, show="•", placeholder_text="Ingrese su contraseña"
        )
        self._campo_password.pack(pady=(0, 24))

        # ── Mensaje de error (oculto por defecto) ───────────────────
        self._label_error = ctk.CTkLabel(
            frame,
            text="",
            text_color=ThemeManager().color("error_text"),
            font=ctk.CTkFont(size=12),
            width=300,
            wraplength=300,
        )
        self._label_error.pack(pady=(0, 12))

        # ── Botón ingresar ──────────────────────────────────────────
        ctk.CTkButton(
            frame,
            text="Ingresar",
            width=300,
            height=42,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._intentar_login,
        ).pack()

    # ── Lógica ─────────────────────────────────────────────────────────────────

    def _intentar_login(self) -> None:
        """Valida las credenciales y navega a home si son correctas."""
        username = self._campo_usuario.get().strip()
        password = self._campo_password.get()

        if not username or not password:
            self._mostrar_error("Por favor complete todos los campos.")
            return

        try:
            usuario = usuario_repo.buscar_por_username(username)
        except RuntimeError as e:
            self._mostrar_error(f"Error de base de datos: {e}")
            return

        # Verificar contraseña con bcrypt (tiempo constante para evitar timing attacks)
        credenciales_validas = (
            usuario is not None
            and bcrypt.checkpw(
                password.encode("utf-8"),
                usuario.password_hash.encode("utf-8"),
            )
        )

        if not credenciales_validas:
            self._mostrar_error("Usuario o contraseña incorrectos.")
            self._campo_password.delete(0, "end")
            self._campo_password.focus()
            return

        Session().iniciar_sesion(usuario)
        self._navigate("home")

    def _mostrar_error(self, mensaje: str) -> None:
        """Muestra un mensaje de error en rojo debajo de los campos."""
        self._label_error.configure(text=mensaje)
