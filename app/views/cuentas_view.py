# -*- coding: utf-8 -*-
"""Vista de administración de cuentas — solo accesible para administradores."""

from collections.abc import Callable

import bcrypt
import customtkinter as ctk

from app.models.usuario import Usuario
from app.repositories import usuario_repo
from app.session import Session
from app.theme import ThemeManager


class CuentasView(ctk.CTkFrame):
    """Frame de administración: listado de cuentas y creación de cajeras."""

    def __init__(self, master: ctk.CTk, navigate: Callable[[str], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self._navigate = navigate

        master.title("Facturación — Administrar Cuentas")
        master.geometry("860x560")
        master.minsize(640, 420)
        master.resizable(True, True)

        self._construir_ui()
        self._cargar_lista()

    def _construir_ui(self) -> None:
        """Construye todos los widgets de la pantalla de administración."""

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
            text="Administrar Cuentas",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=8, pady=10)

        ctk.CTkButton(
            header,
            text="+ Nueva cuenta",
            width=140,
            height=34,
            font=ctk.CTkFont(size=13),
            command=self._abrir_form_nueva_cuenta,
        ).pack(side="right", padx=20, pady=11)

        # ── Lista de cuentas ────────────────────────────────────────
        self._frame_lista = ctk.CTkScrollableFrame(
            self,
            label_text="Cuentas registradas",
            label_font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._frame_lista.pack(fill="both", expand=True, padx=16, pady=12)

    def _cargar_lista(self) -> None:
        """Destruye y re-renderiza la lista de cuentas desde la BD."""
        for widget in self._frame_lista.winfo_children():
            widget.destroy()

        usuarios = usuario_repo.listar_todos()

        if not usuarios:
            ctk.CTkLabel(
                self._frame_lista,
                text="No hay cuentas registradas",
                text_color="gray",
            ).pack(pady=20)
            return

        id_sesion = Session().usuario_actual.id
        for usuario in usuarios:
            self._crear_fila(usuario, id_sesion)

    def _crear_fila(self, usuario: Usuario, id_sesion: int) -> None:
        """Crea una fila en la lista para el usuario dado."""
        fila = ctk.CTkFrame(self._frame_lista)
        fila.pack(fill="x", padx=4, pady=3)
        fila.grid_columnconfigure(0, weight=1)

        # Nombre y username
        ctk.CTkLabel(
            fila,
            text=usuario.nombre,
            anchor="w",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=12, pady=(8, 0))

        ctk.CTkLabel(
            fila,
            text=f"@{usuario.username}",
            anchor="w",
            text_color="gray",
            font=ctk.CTkFont(size=12),
        ).grid(row=1, column=0, sticky="w", padx=12, pady=(0, 8))

        # Badge de rol
        _c = ThemeManager().color
        rol_color = _c("badge_admin") if usuario.es_admin else _c("badge_cajera")
        ctk.CTkLabel(
            fila,
            text=usuario.rol,
            fg_color=rol_color,
            corner_radius=6,
            font=ctk.CTkFont(size=11),
            width=62,
            height=24,
        ).grid(row=0, column=1, rowspan=2, padx=12, pady=8)

        # Botón eliminar: solo visible para cajeras que no sean la sesión activa
        if not usuario.es_admin and usuario.id != id_sesion:
            ctk.CTkButton(
                fila,
                text="Eliminar",
                width=90,
                height=32,
                fg_color="transparent",
                border_width=1,
                text_color=ThemeManager().color("error_text"),
                hover_color=ThemeManager().color("danger_hover"),
                font=ctk.CTkFont(size=12),
                command=lambda u=usuario: self._confirmar_eliminar(u),
            ).grid(row=0, column=2, rowspan=2, padx=(0, 12), pady=8)

    # ── Diálogos ────────────────────────────────────────────────────────────────

    def _confirmar_eliminar(self, usuario: Usuario) -> None:
        """Abre un diálogo modal de confirmación antes de eliminar la cuenta."""
        raiz = self.winfo_toplevel()
        dialogo = ctk.CTkToplevel(raiz)
        dialogo.title("Confirmar eliminación")
        dialogo.resizable(False, False)
        dialogo.transient(raiz)

        ancho, alto = 380, 190
        raiz.update_idletasks()
        x = raiz.winfo_x() + (raiz.winfo_width() - ancho) // 2
        y = raiz.winfo_y() + (raiz.winfo_height() - alto) // 2
        dialogo.geometry(f"{ancho}x{alto}+{x}+{y}")
        dialogo.after(50, dialogo.grab_set)

        ctk.CTkLabel(
            dialogo,
            text=f"¿Eliminar la cuenta de\n{usuario.nombre} (@{usuario.username})?",
            font=ctk.CTkFont(size=14),
            justify="center",
        ).pack(pady=(30, 22))

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
            usuario_repo.eliminar(usuario.id)
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

    def _abrir_form_nueva_cuenta(self) -> None:
        """Abre el formulario modal para registrar una nueva cuenta de cajera."""
        raiz = self.winfo_toplevel()
        dialogo = ctk.CTkToplevel(raiz)
        dialogo.title("Nueva cuenta de cajera")
        dialogo.resizable(False, False)
        dialogo.transient(raiz)

        ancho, alto = 420, 450
        raiz.update_idletasks()
        x = raiz.winfo_x() + (raiz.winfo_width() - ancho) // 2
        y = raiz.winfo_y() + (raiz.winfo_height() - alto) // 2
        dialogo.geometry(f"{ancho}x{alto}+{x}+{y}")
        dialogo.after(50, dialogo.grab_set)

        ctk.CTkLabel(
            dialogo,
            text="Nueva cuenta de cajera",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=(22, 16))

        contenedor = ctk.CTkFrame(dialogo, fg_color="transparent")
        contenedor.pack(fill="x", padx=36)

        ctk.CTkLabel(contenedor, text="Nombre completo", anchor="w").pack(fill="x")
        campo_nombre = ctk.CTkEntry(contenedor, placeholder_text="Ej. María López")
        campo_nombre.pack(fill="x", pady=(4, 12))

        ctk.CTkLabel(contenedor, text="Nombre de usuario", anchor="w").pack(fill="x")
        campo_username = ctk.CTkEntry(contenedor, placeholder_text="Ej. mlopez")
        campo_username.pack(fill="x", pady=(4, 12))

        ctk.CTkLabel(contenedor, text="Contraseña", anchor="w").pack(fill="x")
        campo_password = ctk.CTkEntry(
            contenedor, placeholder_text="Mínimo 6 caracteres", show="•"
        )
        campo_password.pack(fill="x", pady=(4, 12))

        ctk.CTkLabel(contenedor, text="Confirmar contraseña", anchor="w").pack(fill="x")
        campo_confirm = ctk.CTkEntry(
            contenedor, placeholder_text="Repita la contraseña", show="•"
        )
        campo_confirm.pack(fill="x", pady=(4, 8))

        label_error = ctk.CTkLabel(
            contenedor,
            text="",
            text_color=ThemeManager().color("error_text"),
            font=ctk.CTkFont(size=12),
            wraplength=348,
        )
        label_error.pack(fill="x")

        frame_btns = ctk.CTkFrame(dialogo, fg_color="transparent")
        frame_btns.pack(pady=(10, 16))

        ctk.CTkButton(
            frame_btns,
            text="Cancelar",
            width=120,
            fg_color="transparent",
            border_width=1,
            text_color=ThemeManager().color("transparent_btn_text"),
            command=dialogo.destroy,
        ).pack(side="left", padx=8)

        def _crear() -> None:
            nombre = campo_nombre.get().strip()
            username = campo_username.get().strip()
            password = campo_password.get()
            confirm = campo_confirm.get()

            if not nombre or not username or not password:
                label_error.configure(text="Todos los campos son requeridos.")
                return
            if password != confirm:
                label_error.configure(text="Las contraseñas no coinciden.")
                return
            if len(password) < 6:
                label_error.configure(text="La contraseña debe tener mínimo 6 caracteres.")
                return

            try:
                password_hash = bcrypt.hashpw(
                    password.encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8")
                usuario_repo.crear(nombre, username, password_hash, "cajera")
                dialogo.destroy()
                self._cargar_lista()
            except RuntimeError as e:
                label_error.configure(text=str(e))

        ctk.CTkButton(
            frame_btns,
            text="Crear cuenta",
            width=120,
            command=_crear,
        ).pack(side="left", padx=8)

        campo_nombre.after(100, campo_nombre.focus)

    def _volver_a_home(self) -> None:
        self._navigate("home")
