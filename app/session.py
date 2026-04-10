# -*- coding: utf-8 -*-
"""Manejo de la sesión activa del usuario en memoria."""

from datetime import datetime
from typing import Optional

from app.models.usuario import Usuario


class Session:
    """Singleton que mantiene el estado de la sesión durante la ejecución.

    La sesión solo existe en memoria; al cerrar el programa se pierde.
    """

    _instance: Optional["Session"] = None

    def __new__(cls) -> "Session":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._inicializar()
        return cls._instance

    def _inicializar(self) -> None:
        """Establece el estado inicial (sin sesión activa)."""
        self.usuario_actual: Optional[Usuario] = None
        self.inicio_turno: Optional[datetime] = None

    def iniciar_sesion(self, usuario: Usuario) -> None:
        """Guarda el usuario autenticado y registra el inicio del turno."""
        self.usuario_actual = usuario
        self.inicio_turno = datetime.now()

    def cerrar_sesion(self) -> None:
        """Limpia la sesión activa."""
        self.usuario_actual = None
        self.inicio_turno = None

    def esta_autenticado(self) -> bool:
        """Retorna True si hay un usuario con sesión abierta."""
        return self.usuario_actual is not None

    def es_admin(self) -> bool:
        """Retorna True si el usuario activo tiene rol de administrador."""
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.es_admin
