# -*- coding: utf-8 -*-
"""Punto de entrada del sistema de facturación."""

from collections.abc import Callable

import customtkinter as ctk

from app.database.migrations import run_migrations


class App(ctk.CTk):
    """Ventana raíz única. Gestiona la navegación entre vistas."""

    def __init__(self) -> None:
        super().__init__()
        self._frame_actual: ctk.CTkFrame | None = None
        self.navigate("login")

    def navigate(self, destino: str) -> None:
        """Destruye el frame actual y muestra el frame del destino indicado."""
        # Limpiar bindings de la ventana que pertenecen a la vista anterior
        self.unbind("<Return>")

        if self._frame_actual is not None:
            self._frame_actual.destroy()
            self._frame_actual = None

        if destino == "login":
            from app.views.login_view import LoginView
            self._frame_actual = LoginView(self, navigate=self.navigate)
        elif destino == "home":
            from app.views.home_view import HomeView
            self._frame_actual = HomeView(self, navigate=self.navigate)
        elif destino == "facturar":
            from app.views.facturar_view import FacturarView
            self._frame_actual = FacturarView(self, navigate=self.navigate)
        else:
            raise ValueError(f"Destino desconocido: {destino!r}")

        self._frame_actual.pack(fill="both", expand=True)


def main() -> None:
    """Inicializa la aplicación y abre la pantalla de login."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    run_migrations()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
