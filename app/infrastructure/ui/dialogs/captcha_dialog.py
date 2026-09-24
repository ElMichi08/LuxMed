from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.application.dto import DecisionOperador, SolicitudOperador
from app.infrastructure.ui.theme.icons import icono
from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, TIPOGRAFIA

ANCHO = 480
ALTO_CABECERA = 40
TEXTO_TECNICO = (
    "Marcar como error deja al paciente en ERROR_PORTAL_2 y sigue con el siguiente."
)


class CaptchaDialog(QDialog):
    decision_tomada = pyqtSignal(object)

    def __init__(
        self, solicitud: SolicitudOperador, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Verificación del Portal 2 no completada")
        self.setModal(True)
        self.setFixedWidth(ANCHO)

        cabecera = QFrame()
        cabecera.setObjectName("cabecera_dialogo")
        cabecera.setFixedHeight(ALTO_CABECERA)
        disposicion_cabecera = QHBoxLayout(cabecera)
        disposicion_cabecera.setContentsMargins(ESPACIADO.md, 0, ESPACIADO.md, 0)
        disposicion_cabecera.setSpacing(ESPACIADO.sm)
        icono_titulo = QLabel()
        icono_titulo.setPixmap(icono("warning", COLORES.rojo, 18).pixmap(18, 18))
        titulo = QLabel("Verificación del Portal 2 no completada")
        titulo.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_subtitulo,
                TIPOGRAFIA.peso_semibold,
            )
        )
        titulo.setWordWrap(True)
        disposicion_cabecera.addWidget(icono_titulo)
        disposicion_cabecera.addWidget(titulo, 1)

        paciente = solicitud.paciente
        identificacion = (
            f"{paciente.nombre} · {paciente.cedula}" if paciente is not None else ""
        )
        texto = QLabel(
            "El captcha del Portal 2 no se resolvió tras 3 intentos automáticos y una "
            f"verificación manual. Paciente: {identificacion}. ¿Cómo quieres continuar?"
        )
        texto.setWordWrap(True)
        texto.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_subtitulo))

        caja_tecnica = QFrame()
        caja_tecnica.setObjectName("caja_estado_tecnico")
        disposicion_tecnica = QVBoxLayout(caja_tecnica)
        disposicion_tecnica.setContentsMargins(
            ESPACIADO.sm, ESPACIADO.sm, ESPACIADO.sm, ESPACIADO.sm
        )
        nota_tecnica = QLabel(TEXTO_TECNICO)
        nota_tecnica.setWordWrap(True)
        nota_tecnica.setFont(QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_etiqueta))
        nota_tecnica.setStyleSheet(f"color: {COLORES.tinta_sec}; border: none;")
        disposicion_tecnica.addWidget(nota_tecnica)

        cuerpo = QVBoxLayout()
        cuerpo.setContentsMargins(
            ESPACIADO.xl, ESPACIADO.lg, ESPACIADO.xl, ESPACIADO.lg
        )
        cuerpo.setSpacing(ESPACIADO.md)
        cuerpo.addWidget(texto)
        cuerpo.addWidget(caja_tecnica)

        self.boton_marcar_error = QPushButton("Marcar como error y continuar")
        self.boton_marcar_error.setProperty("variante", "secundario")
        self.boton_marcar_error.clicked.connect(self._al_marcar_error)

        self.boton_reintentar = QPushButton("Reintentar")
        self.boton_reintentar.setProperty("variante", "primario")
        self.boton_reintentar.clicked.connect(self._al_reintentar)

        pie = QFrame()
        pie.setObjectName("pie_dialogo")
        disposicion_pie = QHBoxLayout(pie)
        disposicion_pie.setContentsMargins(
            ESPACIADO.md, ESPACIADO.sm, ESPACIADO.md, ESPACIADO.sm
        )
        disposicion_pie.setSpacing(ESPACIADO.sm)
        disposicion_pie.addStretch(1)
        disposicion_pie.addWidget(self.boton_marcar_error)
        disposicion_pie.addWidget(self.boton_reintentar)

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(0)
        disposicion.addWidget(cabecera)
        disposicion.addLayout(cuerpo)
        disposicion.addWidget(pie)

    def _al_reintentar(self) -> None:
        self.decision_tomada.emit(DecisionOperador.REINTENTAR_CAPTCHA)
        self.accept()

    def _al_marcar_error(self) -> None:
        self.decision_tomada.emit(DecisionOperador.MARCAR_ERROR_PORTAL_2)
        self.accept()
