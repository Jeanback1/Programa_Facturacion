# -*- coding: utf-8 -*-
"""Vista de inicio de sesión."""

import bcrypt
import customtkinter as ctk

from app.repositories import usuario_repo
from app.session import Session


class LoginView(ctk.CTk):
    """Ventana de login. Es la raíz de la aplicación CustomTkinter."""

    def __init__(self) -> None:
        super().__init__()

        self.title("Facturación — Iniciar sesión")
        self.resizable(False, False)
        self._centrar_ventana(420, 520)

        self._construir_ui()

        # Enter también dispara el intento de login
        self.bind("<Return>", lambda _event: self._intentar_login())
        self._campo_usuario.focus()

    def _centrar_ventana(self, ancho: int, alto: int) -> None:
        """Posiciona la ventana en el centro de la pantalla."""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry(f"{ancho}x{alto}+{x}+{y}")

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
            text_color="#FF5555",
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
        """Valida las credenciales y abre la pantalla principal si son correctas."""
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

        # Login exitoso — iniciar sesión y abrir home
        Session().iniciar_sesion(usuario)
        self._abrir_home()

    def _mostrar_error(self, mensaje: str) -> None:
        """Muestra un mensaje de error en rojo debajo de los campos."""
        self._label_error.configure(text=mensaje)

    def _abrir_home(self) -> None:
        """Destruye esta ventana y abre la pantalla principal."""
        # Importación diferida para evitar ciclo de importaciones
        from app.views.home_view import HomeView

        self.destroy()
        app = HomeView()
        app.mainloop()
