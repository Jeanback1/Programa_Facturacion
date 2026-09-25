# -*- coding: utf-8 -*-
"""Singleton para la conexión SQLite compartida."""

import sqlite3
from typing import Optional

from app.config import DB_PATH


class _DatabaseConnection:
    """Administra una única conexión SQLite para toda la aplicación."""

    _instance: Optional["_DatabaseConnection"] = None
    _connection: Optional[sqlite3.Connection] = None

    def __new__(cls) -> "_DatabaseConnection":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        """Retorna la conexión activa, creándola si no existe."""
        if self._connection is None:
            try:
                self._connection = sqlite3.connect(str(DB_PATH))
                # Retorna filas como diccionarios accesibles por nombre de columna
                self._connection.row_factory = sqlite3.Row
                # Activar restricciones de clave foránea
                self._connection.execute("PRAGMA foreign_keys = ON")
                self._connection.commit()
            except sqlite3.Error as e:
                raise RuntimeError(f"No se pudo conectar a la base de datos: {e}") from e
        return self._connection

    def close(self) -> None:
        """Cierra la conexión activa."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None


def get_connection() -> sqlite3.Connection:
    """Función de acceso rápido a la conexión compartida."""
    return _DatabaseConnection().get_connection()
