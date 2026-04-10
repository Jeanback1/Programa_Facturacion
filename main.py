# -*- coding: utf-8 -*-
"""Punto de entrada del sistema de facturación."""

import customtkinter as ctk

from app.database.migrations import run_migrations
from app.views.login_view import LoginView


def main() -> None:
    """Inicializa la aplicación y abre la pantalla de login."""
    # Tema oscuro por defecto
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    # Ejecutar migraciones (crea tablas y admin inicial si no existen)
    run_migrations()

    # Abrir pantalla de login e iniciar el loop de eventos
    app = LoginView()
    app.mainloop()


if __name__ == "__main__":
    main()
