from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame

from app.infrastructure.ui.theme.tokens import GEOMETRIA
from app.infrastructure.ui.widgets.base import etiqueta, fila
from app.infrastructure.ui.widgets.spinner import Spinner


class StatusBar(QFrame):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("barra_estado")
        self.setFixedHeight(GEOMETRIA.barra_estado)
        self._spinner = Spinner(12, 2)
        self._spinner.hide()
        self._actividad = etiqueta("")
        self._progreso = etiqueta("")
        for texto in (self._actividad, self._progreso):
            texto.setTextFormat(Qt.TextFormat.RichText)
        layout = fila((12, 0, 12, 0), 8)
        layout.addWidget(self._spinner)
        layout.addWidget(self._actividad)
        layout.addStretch(1)
        layout.addWidget(self._progreso)
        self.setLayout(layout)

    def mostrar_actividad(self, texto: str, en_curso: bool) -> None:
        self._actividad.setText(texto)
        if en_curso:
            self._spinner.iniciar()
        else:
            self._spinner.detener()

    def mostrar_progreso(self, procesados: int, total: int) -> None:
        self._progreso.setText(f"Procesados <b>{procesados} de {total}</b>")
