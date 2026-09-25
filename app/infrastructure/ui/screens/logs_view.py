from __future__ import annotations

import html
import logging
import os

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QPlainTextEdit, QWidget

from app.infrastructure.ui.log_bridge import LineaLog
from app.infrastructure.ui.theme.tokens import COLORES
from app.infrastructure.ui.widgets.base import columna, etiqueta, fila, marco

LINEAS_MAXIMAS = 5000
SIN_ARCHIVO = "Sin archivo de lote"


def _linea_html(linea: LineaLog) -> str:
    color_nivel = COLORES.rojo if linea.nivel >= logging.ERROR else COLORES.tinta
    return (
        f'<span style="color:{COLORES.tinta_ter}">[{linea.texto_hora}]</span>&nbsp;&nbsp;'
        f'<span style="color:{color_nivel};font-weight:600">{linea.nombre_nivel:<5}</span>&nbsp;&nbsp;'
        f'<span style="color:{COLORES.tinta_sec}">[{html.escape(linea.origen)}]</span>&nbsp;&nbsp;'
        f"{html.escape(linea.mensaje)}"
    )


class LogsView(QWidget):
    errores_cambiados = pyqtSignal(int)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("lienzo")
        self._eventos = 0
        self._errores = 0
        self._advertencias = 0
        self._sesion = etiqueta("", "mono")
        textos = columna(espacio=2)
        textos.addWidget(etiqueta("Logs del sistema", "titulo_seccion"))
        textos.addWidget(etiqueta("Bitácora en tiempo real del lote actual · Registro crudo de consola", "mono"))
        cabecera_layout = fila((24, 20, 24, 12))
        cabecera_layout.addLayout(textos, 1)
        cabecera_layout.addWidget(self._sesion)
        cabecera = marco("cabecera_pantalla", cabecera_layout)

        self._consola = QPlainTextEdit()
        self._consola.setReadOnly(True)
        self._consola.setMaximumBlockCount(LINEAS_MAXIMAS)
        self._archivo = etiqueta(SIN_ARCHIVO, "mono")
        self._contador = etiqueta("", "mono")
        pie_layout = fila((12, 0, 12, 0))
        pie_layout.addWidget(self._archivo, 1)
        pie_layout.addWidget(self._contador)
        pie = marco("pie_acciones", pie_layout)
        pie.setFixedHeight(30)
        cuerpo_layout = columna()
        cuerpo_layout.addWidget(self._consola, 1)
        cuerpo_layout.addWidget(pie)
        cuerpo = QFrame()
        cuerpo.setObjectName("panel")
        cuerpo.setLayout(cuerpo_layout)

        layout = columna()
        layout.addWidget(cabecera)
        contenedor = columna((16, 16, 16, 16))
        contenedor.addWidget(cuerpo)
        layout.addLayout(contenedor, 1)
        self.setLayout(layout)
        self.mostrar_sesion("—")
        self._refrescar_contador()

    def mostrar_sesion(self, lote_id: str) -> None:
        self._sesion.setText(f"SESIÓN: {lote_id} · PID: {os.getpid()}")

    def mostrar_archivo(self, ruta: str | None) -> None:
        self._archivo.setText(f"Archivo: {ruta}" if ruta else SIN_ARCHIVO)

    def agregar(self, linea: LineaLog) -> None:
        self._consola.appendHtml(_linea_html(linea))
        self._eventos += 1
        if linea.nivel >= logging.ERROR:
            self._errores += 1
            self.errores_cambiados.emit(self._errores)
        elif linea.nivel >= logging.WARNING:
            self._advertencias += 1
        self._refrescar_contador()

    def reiniciar(self) -> None:
        self._consola.clear()
        self._eventos = self._errores = self._advertencias = 0
        self.errores_cambiados.emit(0)
        self._refrescar_contador()

    def _refrescar_contador(self) -> None:
        self._contador.setText(
            f"{self._eventos} eventos ({self._errores} errores · {self._advertencias} advertencias) · UTF-8"
        )
