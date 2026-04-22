# -*- coding: utf-8 -*-
"""Gestión global del tema visual (dark/light) de la aplicación."""

from typing import Optional

import customtkinter as ctk

_COLORS: dict[str, dict[str, str]] = {
    "danger_bg":    {"dark": "#C0392B", "light": "#E74C3C"},
    "danger_hover": {"dark": "#922B21", "light": "#C0392B"},
    "success":      {"dark": "#2ECC71", "light": "#27AE60"},
    "border":       {"dark": "#555555", "light": "#BBBBBB"},
    "error_text":   {"dark": "#FF5555", "light": "#CC0000"},
    "badge_admin":  {"dark": "#6E2C00", "light": "#D35400"},
    "badge_cajera":          {"dark": "#1A5276", "light": "#2980B9"},
    "transparent_btn_text":  {"dark": "#DCE4EE", "light": "#1A1A1A"},
}


class ThemeManager:
    """Singleton que mantiene el modo visual activo y provee colores por nombre semántico."""

    _instance: Optional["ThemeManager"] = None

    def __new__(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._mode = "dark"
        return cls._instance

    def apply(self, mode: str) -> None:
        """Aplica el modo indicado ('dark' o 'light') a nivel global de CTk."""
        self._mode = mode
        ctk.set_appearance_mode(mode)

    def toggle(self) -> str:
        """Alterna entre dark y light, persiste la elección en la BD y retorna el nuevo modo."""
        from app.repositories import configuracion_repo
        new_mode = "light" if self._mode == "dark" else "dark"
        self.apply(new_mode)
        configuracion_repo.set("theme_mode", new_mode)
        return new_mode

    @property
    def mode(self) -> str:
        """Retorna el modo activo: 'dark' o 'light'."""
        return self._mode

    def color(self, key: str) -> str:
        """Retorna el color hex para la clave semántica dada en el modo actual."""
        return _COLORS[key][self._mode]
