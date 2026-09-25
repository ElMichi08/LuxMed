from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QFormLayout, QLineEdit, QWidget

from app.domain.entities import CredencialesPortal3
from app.infrastructure.ui.theme.tokens import GEOMETRIA
from app.infrastructure.ui.widgets.base import (
    boton,
    columna,
    establecer_propiedad,
    etiqueta,
    fila,
)
from app.infrastructure.ui.widgets.controles import PasswordField
from app.infrastructure.ui.widgets.paneles import Panel

ANCHO_PANEL = 760
ALTO_CONTROL = 36


def _seccion(titulo: str, ayuda: str) -> Panel:
    panel = Panel(espacio=8)
    panel.setFixedWidth(ANCHO_PANEL)
    panel.contenido.addWidget(etiqueta(titulo, "titulo_seccion"))
    texto = etiqueta(ayuda, "ayuda")
    texto.setWordWrap(True)
    panel.contenido.addWidget(texto)
    panel.contenido.addSpacing(8)
    return panel


class SettingsView(QWidget):
    carpeta_cambiada = pyqtSignal(str)
    credenciales_guardadas = pyqtSignal(object)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("lienzo")
        self._carpeta = QLineEdit()
        self._carpeta.setReadOnly(True)
        self._carpeta.setProperty("solo_lectura", True)
        self._carpeta.setFixedHeight(ALTO_CONTROL)
        self.boton_carpeta = boton("Cambiar…", nombre_icono="folder_open", alto=ALTO_CONTROL)
        self.boton_carpeta.clicked.connect(self._elegir_carpeta)
        carpeta = _seccion(
            "Carpeta de salida",
            "Aquí se guardan el Excel limpio, el Excel auditado y los PDF consolidados de cada lote.",
        )
        control = fila(espacio=12)
        control.addWidget(self._carpeta, 1)
        control.addWidget(self.boton_carpeta)
        carpeta.contenido.addLayout(control)

        self._usuario = QLineEdit()
        self._contrasena = PasswordField()
        for campo in (self._usuario, self._contrasena):
            campo.setFixedHeight(ALTO_CONTROL)
        self.boton_guardar = boton("Guardar credenciales", "primario", alto=GEOMETRIA.boton)
        self.boton_guardar.clicked.connect(self._guardar)
        self._estado_credenciales = etiqueta("", "ayuda")
        credenciales = _seccion(
            "Credenciales del Portal 3",
            "Se usan para iniciar sesión en el Portal 3 con cada paciente. "
            "Se guardan en el archivo .env de este equipo y se aplican al iniciar la próxima campaña.",
        )
        formulario = QFormLayout()
        formulario.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        formulario.setHorizontalSpacing(16)
        formulario.setVerticalSpacing(10)
        formulario.addRow(etiqueta("Usuario", "ayuda"), self._usuario)
        formulario.addRow(etiqueta("Contraseña", "ayuda"), self._contrasena)
        credenciales.contenido.addLayout(formulario)
        acciones = fila(espacio=12)
        acciones.addWidget(self._estado_credenciales, 1)
        acciones.addWidget(self.boton_guardar)
        credenciales.contenido.addSpacing(4)
        credenciales.contenido.addLayout(acciones)

        layout = columna((24, 24, 24, 24), 16)
        layout.addWidget(etiqueta("Ajustes", "titulo"))
        layout.addSpacing(4)
        layout.addWidget(carpeta)
        layout.addWidget(credenciales)
        layout.addStretch(1)
        self.setLayout(layout)

    def mostrar_carpeta(self, ruta: str) -> None:
        self._carpeta.setText(ruta)

    def mostrar_credenciales(self, credenciales: CredencialesPortal3) -> None:
        self._usuario.setText(credenciales.usuario)
        self._contrasena.setText(credenciales.contrasena)
        establecer_propiedad(self._estado_credenciales, "rol", "ayuda")
        self._estado_credenciales.setText(
            "" if credenciales.completas else "Aún no hay credenciales guardadas."
        )

    def confirmar_guardado(self, mensaje: str, exito: bool) -> None:
        establecer_propiedad(self._estado_credenciales, "rol", "exito" if exito else "error")
        self._estado_credenciales.setText(mensaje)

    def _elegir_carpeta(self) -> None:
        ruta = QFileDialog.getExistingDirectory(self, "Elegir carpeta de salida", self._carpeta.text())
        if ruta:
            self.carpeta_cambiada.emit(ruta)

    def _guardar(self) -> None:
        credenciales = CredencialesPortal3(self._usuario.text().strip(), self._contrasena.text())
        if not credenciales.completas:
            self.confirmar_guardado("Completa usuario y contraseña.", exito=False)
            return
        self.credenciales_guardadas.emit(credenciales)
