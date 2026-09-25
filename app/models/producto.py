# -*- coding: utf-8 -*-
"""Modelo de datos para productos del catálogo."""

from dataclasses import dataclass, field

# Constantes de grupos de variante
GRUPO_GUARNICION = 1   # solo modifica el nombre; sin efecto en precio
GRUPO_COMER_LLEVAR = 2  # nombre + precio (reemplaza el precio base)


@dataclass
class ProductoVariante:
    """Variante de un producto.

    grupo: GRUPO_GUARNICION (1) = guarnición, solo altera el nombre.
           GRUPO_COMER_LLEVAR (2) = comer aquí / llevar, altera nombre y precio.
    """

    id: int
    producto_id: int
    nombre: str
    precio: float
    grupo: int = GRUPO_COMER_LLEVAR


@dataclass
class Producto:
    """Representa un producto del catálogo."""

    id: int
    nombre: str
    precio: float
    variantes: list[ProductoVariante] = field(default_factory=list)

    @property
    def guarniciones(self) -> list[ProductoVariante]:
        """Variantes de grupo 1 (solo nombre)."""
        return [v for v in self.variantes if v.grupo == GRUPO_GUARNICION]

    @property
    def comer_llevar(self) -> list[ProductoVariante]:
        """Variantes de grupo 2 (nombre + precio)."""
        return [v for v in self.variantes if v.grupo == GRUPO_COMER_LLEVAR]

    @property
    def tiene_variantes(self) -> bool:
        """True si el producto define alguna variante (de cualquier grupo)."""
        return bool(self.variantes)