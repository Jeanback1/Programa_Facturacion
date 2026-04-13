# -*- coding: utf-8 -*-
"""Vista de configuración del local e impresora."""

from collections.abc import Callable

import customtkinter as ctk

from app.repositories import configuracion_repo

# Campos del formulario: (clave_bd, etiqueta, placeholder)
_CAMPOS: list[tuple[str, str, str]] = [
    ("nombre_local",     "Nombre del local",       "Ej: Colmado Don Pepe"),
    ("direccion",        "Dirección",               "Calle, sector, ciudad"),
    ("telefono",         "Teléfono",                "Ej: 809-555-0000"),
    ("rnc",              "RNC / Cédula fiscal",     "Opcional"),
    ("mensaje_pie",      "Mensaje de cierre",       "Ej: ¡Gracias por su compra!"),
    ("impresora_nombre", "Nombre de la impresora",  "Ej: EPSON TM-T20II"),
]


class ConfiguracionView(ctk.CTkFrame):
    """Pantalla de ajustes del negocio e impresora (solo admin)."""

    def __init__(self, master: ctk.CTk, navigate: Callable[[str], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self._navigate = navigate

        master.title("Facturación — Configuración")
        master.geometry("640x560")
        master.resizable(False, False)

        self._entradas: dict[str, ctk.CTkEntry] = {}
        self._construir_ui()
        self._cargar_valores()

    def _construir_ui(self) -> None:
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
            font=ctk.CTkFont(size=18),
            command=lambda: self._navigate("home"),
        ).pack(side="left", padx=16, pady=10)

        ctk.CTkLabel(
            header,
            text="Configuración del local",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left", padx=8, pady=14)

        # ── Formulario ──────────────────────────────────────────────
        form = ctk.CTkScrollableFrame(self)
        form.pack(fill="both", expand=True, padx=24, pady=16)
        form.grid_columnconfigure(0, weight=1)

        for idx, (clave, etiqueta, placeholder) in enumerate(_CAMPOS):
            ctk.CTkLabel(
                form,
                text=etiqueta,
                font=ctk.CTkFont(size=13),
                anchor="w",
            ).grid(row=idx * 2, column=0, sticky="w", pady=(10, 2))

            entry = ctk.CTkEntry(
                form,
                placeholder_text=placeholder,
                height=38,
            )
            entry.grid(row=idx * 2 + 1, column=0, sticky="ew", pady=(0, 4))
            self._entradas[clave] = entry

        ctk.CTkLabel(
            form,
            text="* El nombre de la impresora debe coincidir exactamente con el que aparece\n"
                 "  en Windows → Panel de control → Dispositivos e impresoras.",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w",
            justify="left",
        ).grid(row=len(_CAMPOS) * 2, column=0, sticky="w", pady=(4, 12))

        # ── Pie con botón Guardar ────────────────────────────────────
        frame_btn = ctk.CTkFrame(self, fg_color="transparent")
        frame_btn.pack(fill="x", padx=24, pady=(0, 20))

        self._lbl_estado = ctk.CTkLabel(
            frame_btn,
            text="",
            font=ctk.CTkFont(size=13),
        )
        self._lbl_estado.pack(side="left", padx=4)

        ctk.CTkButton(
            frame_btn,
            text="Guardar",
            width=140,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._guardar,
        ).pack(side="right")

    def _cargar_valores(self) -> None:
        """Rellena los campos con la configuración guardada en la BD."""
        config = configuracion_repo.get_all()
        for clave, entry in self._entradas.items():
            valor = config.get(clave, "")
            if valor:
                entry.delete(0, "end")
                entry.insert(0, valor)

    def _guardar(self) -> None:
        """Persiste todos los campos del formulario en la BD."""
        for clave, entry in self._entradas.items():
            configuracion_repo.set(clave, entry.get().strip())
        self._lbl_estado.configure(text="Guardado ✓", text_color="#2ECC71")
        self.after(2000, lambda: self._lbl_estado.configure(text=""))
