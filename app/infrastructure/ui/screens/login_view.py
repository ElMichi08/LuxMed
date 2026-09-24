from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.infrastructure.ui.theme.icons import icono
from app.infrastructure.ui.theme.stylesheet import repolish
from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, TIPOGRAFIA
from app.infrastructure.ui.widgets.card import Card

LADO_MONOGRAMA = 28
ANCHO_TARJETA = 400


class LoginView(QWidget):
    intento_ingreso = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._tarjeta = Card()
        self._tarjeta.setFixedWidth(ANCHO_TARJETA)

        cabecera = QHBoxLayout()
        cabecera.setSpacing(ESPACIADO.sm)
        monograma = QLabel("L")
        monograma.setObjectName("monograma")
        monograma.setFixedSize(LADO_MONOGRAMA, LADO_MONOGRAMA)
        monograma.setAlignment(Qt.AlignmentFlag.AlignCenter)
        marca = QLabel("LuxMed")
        marca.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_subtitulo,
                TIPOGRAFIA.peso_semibold,
            )
        )
        cabecera.addWidget(monograma)
        cabecera.addWidget(marca)
        cabecera.addStretch(1)
        self._tarjeta.disposicion_contenido().addLayout(cabecera)

        titulo = QLabel("Acceso local")
        titulo.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_titulo_grande,
                TIPOGRAFIA.peso_semibold,
            )
        )
        self._tarjeta.agregar(titulo)

        subtitulo = QLabel("Ingresa con tu usuario de este equipo.")
        subtitulo.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_subtitulo))
        subtitulo.setStyleSheet(f"color: {COLORES.tinta_sec};")
        self._tarjeta.agregar(subtitulo)

        etiqueta_usuario = QLabel("Usuario")
        etiqueta_usuario.setFont(
            QFont(
                TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base, TIPOGRAFIA.peso_medio
            )
        )
        etiqueta_usuario.setStyleSheet(f"color: {COLORES.tinta_sec};")
        self._campo_usuario = QLineEdit()
        self._campo_usuario.setFont(
            QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_base)
        )
        self._campo_usuario.setFixedHeight(36)
        self._campo_usuario.returnPressed.connect(self._emitir_intento)
        self._tarjeta.agregar(etiqueta_usuario)
        self._tarjeta.agregar(self._campo_usuario)

        etiqueta_contrasena = QLabel("Contraseña")
        etiqueta_contrasena.setFont(
            QFont(
                TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base, TIPOGRAFIA.peso_medio
            )
        )
        etiqueta_contrasena.setStyleSheet(f"color: {COLORES.tinta_sec};")
        self._campo_contrasena = QLineEdit()
        self._campo_contrasena.setFont(
            QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_base)
        )
        self._campo_contrasena.setFixedHeight(36)
        self._campo_contrasena.setEchoMode(QLineEdit.EchoMode.Password)
        self._campo_contrasena.returnPressed.connect(self._emitir_intento)
        accion_ojo = self._campo_contrasena.addAction(
            icono("visibility_off", COLORES.tinta_sec, 16),
            QLineEdit.ActionPosition.TrailingPosition,
        )
        assert accion_ojo is not None
        self._accion_ojo: QAction = accion_ojo
        self._accion_ojo.triggered.connect(self._alternar_visibilidad_contrasena)
        self._tarjeta.agregar(etiqueta_contrasena)
        self._tarjeta.agregar(self._campo_contrasena)

        self._etiqueta_error = QLabel("")
        self._etiqueta_error.setFont(
            QFont(
                TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base, TIPOGRAFIA.peso_medio
            )
        )
        self._etiqueta_error.setStyleSheet(f"color: {COLORES.rojo};")
        self._etiqueta_error.hide()
        self._tarjeta.agregar(self._etiqueta_error)

        self._boton_entrar = QPushButton("Entrar")
        self._boton_entrar.setProperty("variante", "primario")
        self._boton_entrar.setFixedHeight(36)
        self._boton_entrar.clicked.connect(self._emitir_intento)
        self._tarjeta.agregar(self._boton_entrar)

        version = QLabel("Versión 1.0.0")
        version.setFont(QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_etiqueta))
        version.setStyleSheet(f"color: {COLORES.tinta_ter};")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._tarjeta.agregar(version)

        disposicion = QVBoxLayout(self)
        disposicion.addStretch(1)
        fila_central = QHBoxLayout()
        fila_central.addStretch(1)
        fila_central.addWidget(self._tarjeta)
        fila_central.addStretch(1)
        disposicion.addLayout(fila_central)
        disposicion.addStretch(1)

    def usuario(self) -> str:
        return self._campo_usuario.text()

    def contrasena(self) -> str:
        return self._campo_contrasena.text()

    def mostrar_error(self, mensaje: str) -> None:
        self._etiqueta_error.setText(mensaje)
        self._etiqueta_error.show()
        self._campo_contrasena.setProperty("error", True)
        repolish(self._campo_contrasena)

    def limpiar_error(self) -> None:
        self._etiqueta_error.hide()
        self._campo_contrasena.setProperty("error", False)
        repolish(self._campo_contrasena)

    def establecer_cargando(self, cargando: bool) -> None:
        self._boton_entrar.setEnabled(not cargando)
        self._campo_usuario.setEnabled(not cargando)
        self._campo_contrasena.setEnabled(not cargando)
        self._boton_entrar.setText("Entrando…" if cargando else "Entrar")

    def _alternar_visibilidad_contrasena(self) -> None:
        oculta = self._campo_contrasena.echoMode() == QLineEdit.EchoMode.Password
        modo = QLineEdit.EchoMode.Normal if oculta else QLineEdit.EchoMode.Password
        self._campo_contrasena.setEchoMode(modo)
        nombre_icono = "visibility" if oculta else "visibility_off"
        self._accion_ojo.setIcon(icono(nombre_icono, COLORES.tinta_sec, 16))

    def _emitir_intento(self) -> None:
        self.intento_ingreso.emit()
