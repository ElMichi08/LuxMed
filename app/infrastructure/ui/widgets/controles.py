from __future__ import annotations

from collections.abc import Sequence

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QButtonGroup, QFrame, QLineEdit, QPushButton, QWidget

from app.infrastructure.ui.theme.icons import icono
from app.infrastructure.ui.theme.tokens import COLORES, GEOMETRIA
from app.infrastructure.ui.widgets.base import fila

TEXTO_BUSQUEDA = "Buscar por cédula o nombre"


class SearchField(QLineEdit):
    def __init__(self, ancho: int = 280) -> None:
        super().__init__()
        self.setPlaceholderText(TEXTO_BUSQUEDA)
        self.setFixedSize(ancho, GEOMETRIA.campo)
        self.setClearButtonEnabled(True)
        self.addAction(icono("search", COLORES.tinta_ter, 16), QLineEdit.ActionPosition.LeadingPosition)


class OpcionesExclusivas(QWidget):
    cambiado = pyqtSignal(str)

    def __init__(self, opciones: Sequence[tuple[str, str]], variante: str) -> None:
        super().__init__()
        self._grupo = QButtonGroup(self)
        self._grupo.setExclusive(True)
        self._botones: dict[str, QPushButton] = {}
        self._etiquetas = dict(opciones)
        for posicion, (clave, texto) in enumerate(opciones):
            boton = QPushButton(texto)
            boton.setCheckable(True)
            boton.setProperty("variante", variante)
            boton.setProperty("ultimo", posicion == len(opciones) - 1)
            boton.clicked.connect(lambda _marcado, clave=clave: self.cambiado.emit(clave))
            self._grupo.addButton(boton)
            self._botones[clave] = boton
        self._botones[opciones[0][0]].setChecked(True)

    @property
    def botones(self) -> list[QPushButton]:
        return list(self._botones.values())

    @property
    def seleccion(self) -> str:
        return next(clave for clave, boton in self._botones.items() if boton.isChecked())

    def seleccionar(self, clave: str) -> None:
        self._botones[clave].setChecked(True)
        self.cambiado.emit(clave)

    def establecer_contador(self, clave: str, cantidad: int) -> None:
        self._botones[clave].setText(f"{self._etiquetas[clave]}  {cantidad}")


class SegmentedFilter(OpcionesExclusivas):
    def __init__(self, opciones: Sequence[tuple[str, str]]) -> None:
        super().__init__(opciones, "segmento")
        contenedor = QFrame()
        contenedor.setObjectName("segmentos")
        contenedor.setFixedHeight(GEOMETRIA.campo)
        interno = fila()
        for boton in self.botones:
            interno.addWidget(boton)
        contenedor.setLayout(interno)
        externo = fila()
        externo.addWidget(contenedor, 0, Qt.AlignmentFlag.AlignVCenter)
        self.setLayout(externo)


class Tabs(OpcionesExclusivas):
    def __init__(self, opciones: Sequence[tuple[str, str]]) -> None:
        super().__init__(opciones, "pestana")
        layout = fila()
        for boton in self.botones:
            boton.setFixedHeight(36)
            layout.addWidget(boton)
        self.setLayout(layout)


class PasswordField(QLineEdit):
    def __init__(self) -> None:
        super().__init__()
        self.setEchoMode(QLineEdit.EchoMode.Password)
        self._alternar = QAction(self)
        self._alternar.setToolTip("Mostrar u ocultar la contraseña")
        self._alternar.triggered.connect(self._cambiar_visibilidad)
        self.addAction(self._alternar, QLineEdit.ActionPosition.TrailingPosition)
        self._refrescar_icono()

    def _cambiar_visibilidad(self) -> None:
        oculta = self.echoMode() is QLineEdit.EchoMode.Password
        self.setEchoMode(QLineEdit.EchoMode.Normal if oculta else QLineEdit.EchoMode.Password)
        self._refrescar_icono()

    def _refrescar_icono(self) -> None:
        oculta = self.echoMode() is QLineEdit.EchoMode.Password
        self._alternar.setIcon(icono("visibility" if oculta else "visibility_off", COLORES.tinta_sec, 16))
