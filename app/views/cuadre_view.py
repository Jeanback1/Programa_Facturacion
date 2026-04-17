# -*- coding: utf-8 -*-
"""Vista de cuadre — lista de facturas pendientes e historial de cuadres."""

from collections.abc import Callable

import customtkinter as ctk

from app.database.connection import get_connection
from app.theme import ThemeManager
from app.models.cuadre import Cuadre
from app.models.factura import Factura
from app.repositories import cuadre_repo, factura_item_repo, factura_repo
from app.session import Session


class CuadreView(ctk.CTkFrame):
    """Frame de cuadre con panel izquierdo de facturas pendientes y panel derecho de historial."""

    def __init__(self, master: ctk.CTk, navigate: Callable[[str], None]) -> None:
        super().__init__(master, fg_color="transparent")
        self._navigate = navigate

        master.title("Facturación — Cuadre")
        master.geometry("1100x680")
        master.minsize(900, 500)
        master.resizable(True, True)

        self._usuario_id: int = Session().usuario_actual.id
        self._facturas: list[Factura] = []
        self._cuadres: list[Cuadre] = []

        self._construir_ui()
        self._cargar_datos()

    def _construir_ui(self) -> None:
        """Construye el skeleton estático de la UI."""

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
            text="Cuadre",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(side="left", padx=8, pady=10)

        # ── Body (dos columnas) ─────────────────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        body.grid_columnconfigure(0, weight=4)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # ── Columna izquierda — Facturas pendientes ─────────────────
        col_izquierda = ctk.CTkFrame(body, fg_color="transparent")
        col_izquierda.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        col_izquierda.grid_rowconfigure(0, weight=1)
        col_izquierda.grid_columnconfigure(0, weight=1)

        self._frame_facturas = ctk.CTkScrollableFrame(
            col_izquierda,
            label_text="Facturas pendientes",
            label_font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._frame_facturas.grid(row=0, column=0, sticky="nsew", pady=(0, 8))

        frame_btn = ctk.CTkFrame(col_izquierda, fg_color="transparent")
        frame_btn.grid(row=1, column=0, sticky="ew")
        frame_btn.grid_columnconfigure(0, weight=1)
        frame_btn.grid_columnconfigure(1, weight=0)

        # Label con el total
        self._lbl_total = ctk.CTkLabel(
            frame_btn,
            text="Total: $0",
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        self._lbl_total.grid(row=0, column=0, padx=(8, 0), pady=8, sticky="w")

        self._btn_cuadrar = ctk.CTkButton(
            frame_btn,
            text="Cuadrar",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=44,
            state="disabled",
            command=self._cuadrar,
        )
        self._btn_cuadrar.grid(row=0, column=1, padx=(0, 8), pady=8, sticky="e")

        # ── Columna derecha — Historial ────────────────────────────
        col_derecha = ctk.CTkFrame(body)
        col_derecha.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        col_derecha.grid_columnconfigure(0, weight=1)
        col_derecha.grid_rowconfigure(0, weight=1)

        self._frame_cuadres = ctk.CTkScrollableFrame(
            col_derecha,
            label_text="Historial",
            label_font=ctk.CTkFont(size=13, weight="bold"),
        )
        self._frame_cuadres.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)

    # ── Datos ───────────────────────────────────────────────────────────────────

    def _cargar_datos(self) -> None:
        """Carga facturas y cuadres desde la BD y refresca ambos paneles."""
        self._facturas = factura_repo.listar_sin_cuadrar(self._usuario_id)
        self._cuadres = cuadre_repo.listar_por_usuario(self._usuario_id)
        self._renderizar_facturas()
        self._renderizar_cuadres()
        self._actualizar_estado_boton()
        self._actualizar_total()

    # ── Renderizado ─────────────────────────────────────────────────────────────

    def _renderizar_facturas(self) -> None:
        """Limpia y re-renderiza el panel de facturas pendientes."""
        for widget in self._frame_facturas.winfo_children():
            widget.destroy()

        if not self._facturas:
            ctk.CTkLabel(
                self._frame_facturas,
                text="No hay facturas pendientes",
                text_color="gray",
                font=ctk.CTkFont(size=13),
            ).pack(pady=24)
            return

        for factura in self._facturas:
            self._crear_fila_factura(factura)

    def _crear_fila_factura(self, factura: Factura) -> None:
        """Crea una fila para una factura en el panel izquierdo."""
        fila = ctk.CTkFrame(
            self._frame_facturas,
            height=44,
            border_width=1,
            border_color=ThemeManager().color("border"),
            corner_radius=6,
        )
        fila.pack(fill="x", padx=8, pady=3)
        fila.pack_propagate(False)
        fila.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(
            fila,
            text=f"#{factura.id}",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=50,
            anchor="center",
        ).grid(row=0, column=0, padx=(8, 4), pady=4)

        detalle_texto = (factura.detalle or "")[:25]
        lbl_detalle = ctk.CTkLabel(
            fila,
            text=detalle_texto,
            font=ctk.CTkFont(size=12),
            anchor="w",
            width=120,
            cursor="hand2",
        )
        lbl_detalle.grid(row=0, column=1, padx=4, pady=4, sticky="w")
        lbl_detalle.bind("<Button-1>", lambda _e, f=factura: self._abrir_detalle(f))

        ctk.CTkLabel(
            fila,
            text=factura.hora_facturacion[11:16],
            font=ctk.CTkFont(size=13),
            anchor="w",
        ).grid(row=0, column=2, padx=4, pady=4, sticky="w")

        ctk.CTkLabel(
            fila,
            text=f"${factura.total:,.0f}",
            font=ctk.CTkFont(size=13, weight="bold"),
            width=90,
            anchor="e",
        ).grid(row=0, column=3, padx=(4, 8), pady=4)

        ctk.CTkButton(
            fila,
            text="re-imprimir",
            width=80,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            command=lambda f=factura: self._reimprimir_factura(f),
        ).grid(row=0, column=4, padx=(0, 4), pady=4)

        ctk.CTkButton(
            fila,
            text="Detalles",
            width=80,
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            border_width=1,
            command=lambda f=factura: self._ver_detalles(f),
        ).grid(row=0, column=5, padx=(0, 8), pady=4)

    def _renderizar_cuadres(self) -> None:
        """Limpia y re-renderiza el historial de cuadres."""
        for widget in self._frame_cuadres.winfo_children():
            widget.destroy()

        if not self._cuadres:
            ctk.CTkLabel(
                self._frame_cuadres,
                text="Sin cuadres previos",
                text_color="gray",
                font=ctk.CTkFont(size=12),
            ).pack(pady=16)
            return

        for cuadre in self._cuadres:
            self._crear_fila_cuadre(cuadre)

    def _crear_fila_cuadre(self, cuadre: Cuadre) -> None:
        """Crea una fila compacta con la fecha a la izquierda y el total a la derecha"""
        fila = ctk.CTkFrame(
            self._frame_cuadres,
            border_width=1,
            border_color=ThemeManager().color("border"),
            corner_radius=6,
        )
        fila.pack(fill="x", padx=4, pady=3)

        # Texto a la izquierda (Fecha/Hora)
        ctk.CTkLabel(
            fila,
            text=cuadre.hora_cuadre[:16],
            font=ctk.CTkFont(size=11),
        ).pack(side="left", padx=10, pady=8)

        # Texto a la derecha (Total)
        ctk.CTkLabel(
            fila,
            text=f"${cuadre.total_cuadre:,.0f}",
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="right", padx=10, pady=8)

    def _actualizar_estado_boton(self) -> None:
        """Habilita o deshabilita el botón Cuadrar según si hay facturas pendientes."""
        self._btn_cuadrar.configure(state="normal" if self._facturas else "disabled")

    def _actualizar_total(self) -> None:
        """Actualiza el label con el total acumulado de las facturas pendientes."""
        total = sum(f.total for f in self._facturas)
        self._lbl_total.configure(text=f"Total: ${total:,.0f}")

    # ── Acciones ────────────────────────────────────────────────────────────────

    def _ver_detalles(self, factura: Factura) -> None:
        """Abre popup modal con los ítems de la factura seleccionada."""
        raiz = self.winfo_toplevel()
        dialogo = ctk.CTkToplevel(raiz)
        dialogo.title(f"Detalles — Factura #{factura.id}")
        dialogo.resizable(False, False)
        dialogo.transient(raiz)

        ancho, alto = 460, 420
        raiz.update_idletasks()
        x = raiz.winfo_x() + (raiz.winfo_width() - ancho) // 2
        y = raiz.winfo_y() + (raiz.winfo_height() - alto) // 2
        dialogo.geometry(f"{ancho}x{alto}+{x}+{y}")
        dialogo.after(50, dialogo.grab_set)

        ctk.CTkLabel(
            dialogo,
            text=f"Factura #{factura.id}",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).pack(pady=(16, 2))

        ctk.CTkLabel(
            dialogo,
            text=f"{factura.hora_facturacion[:16]}  |  Total: ${factura.total:,.0f}",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(pady=(0, 8))

        lista = ctk.CTkScrollableFrame(dialogo, height=280)
        lista.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        items = factura_item_repo.listar_por_factura(factura.id)
        if not items:
            ctk.CTkLabel(lista, text="Sin ítems", text_color="gray").pack(pady=12)
        else:
            for item in items:
                fila = ctk.CTkFrame(lista, fg_color="transparent")
                fila.pack(fill="x", pady=2)
                fila.grid_columnconfigure(1, weight=1)

                ctk.CTkLabel(
                    fila,
                    text=str(item.cantidad),
                    font=ctk.CTkFont(size=13, weight="bold"),
                    width=32,
                    anchor="center",
                ).grid(row=0, column=0, padx=(4, 8))

                ctk.CTkLabel(
                    fila,
                    text=item.nombre,
                    font=ctk.CTkFont(size=13),
                    anchor="w",
                ).grid(row=0, column=1, sticky="ew", padx=4)

                ctk.CTkLabel(
                    fila,
                    text=f"${item.subtotal:,.0f}",
                    font=ctk.CTkFont(size=13, weight="bold"),
                    width=80,
                    anchor="e",
                ).grid(row=0, column=2, padx=(4, 4))

        ctk.CTkButton(
            dialogo,
            text="Cerrar",
            width=120,
            command=dialogo.destroy,
        ).pack(pady=(0, 16))

    def _abrir_detalle(self, factura: Factura) -> None:
        """Abre popup con el detalle completo de la factura."""
        raiz = self.winfo_toplevel()
        dialogo = ctk.CTkToplevel(raiz)
        dialogo.title(f"Detalle — Factura #{factura.id}")
        dialogo.resizable(False, False)
        dialogo.transient(raiz)

        ancho, alto = 360, 200
        raiz.update_idletasks()
        x = raiz.winfo_x() + (raiz.winfo_width() - ancho) // 2
        y = raiz.winfo_y() + (raiz.winfo_height() - alto) // 2
        dialogo.geometry(f"{ancho}x{alto}+{x}+{y}")
        dialogo.after(50, dialogo.grab_set)

        ctk.CTkLabel(
            dialogo,
            text=f"Factura #{factura.id}",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(pady=(16, 6))

        texto = ctk.CTkTextbox(dialogo, height=80)
        texto.pack(fill="x", padx=16, pady=(0, 8))
        texto.insert("1.0", factura.detalle or "(sin detalle)")
        texto.configure(state="disabled")

        ctk.CTkButton(dialogo, text="Cerrar", width=100, command=dialogo.destroy).pack(pady=(0, 16))

    def _reimprimir_factura(self, factura: Factura) -> None:
        """Reimprime el recibo de una factura ya registrada."""
        try:
            from app.printing import impresora
            from app.repositories import configuracion_repo

            items_db = factura_item_repo.listar_por_factura(factura.id)
            items = {
                item.id: {
                    "nombre": item.nombre,
                    "precio_unitario": item.precio_unitario,
                    "cantidad": item.cantidad,
                }
                for item in items_db
            }
            config = configuracion_repo.get_all()
            nombre_cajera = Session().usuario_actual.nombre
            impresora.imprimir_recibo(
                factura=factura,
                items=items,
                config=config,
                nombre_cajera=nombre_cajera,
                detalle=factura.detalle,
                direccion=factura.direccion,
                es_copia=True,
            )
        except RuntimeError as e:
            from tkinter import messagebox
            messagebox.showerror("Error de impresión", str(e))

    def _cuadrar(self) -> None:
        """Crea un cuadre agrupando todas las facturas pendientes del usuario (transacción atómica)."""
        if not self._facturas:
            return

        facturas_cuadradas = list(self._facturas)
        total = sum(f.total for f in facturas_cuadradas)
        conn = get_connection()
        try:
            cur = conn.execute(
                "INSERT INTO cuadres (usuario_id, total_cuadre) VALUES (?, ?)",
                (self._usuario_id, total),
            )
            cuadre_id_nuevo = cur.lastrowid
            conn.execute(
                "UPDATE facturas SET cuadre_id = ? WHERE cuadre_id IS NULL AND usuario_id = ?",
                (cuadre_id_nuevo, self._usuario_id),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            self._btn_cuadrar.configure(text="Error", fg_color=ThemeManager().color("danger_bg"))
            self.after(
                2000,
                lambda: self._btn_cuadrar.configure(
                    text="Cuadrar", fg_color=["#3B8ED0", "#1F6AA5"]
                ),
            )
            return

        self._cargar_datos()

        try:
            from datetime import datetime

            from app.printing.impresora import imprimir_cuadre
            from app.repositories import configuracion_repo

            config = configuracion_repo.get_all()
            nombre_cajera = Session().usuario_actual.nombre
            hora_cuadre = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            imprimir_cuadre(
                facturas_cuadradas,
                cuadre_id_nuevo,
                hora_cuadre,
                nombre_cajera,
                config,
                total,
            )
        except RuntimeError:
            pass  # impresora no configurada o inaccesible — el cuadre ya fue guardado
