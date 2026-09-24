from __future__ import annotations

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

from app.infrastructure.ui.theme.icons import icono
from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, TIPOGRAFIA

ANCHO = 480
ALTO_CABECERA = 48
TITULO = "¿Cerrar con un lote en curso?"
TEXTO_EXPLICATIVO = (
    "Si cierras ahora, el lote se detendrá. Los pacientes ya procesados se conservan; "
    "los pendientes quedarán sin completar y podrás continuarlos iniciando un lote nuevo "
    "con el mismo listado."
)


class CloseConfirmationDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(TITULO)
        self.setModal(True)
        self.setFixedWidth(ANCHO)

        cabecera = QFrame()
        cabecera.setObjectName("cabecera_dialogo")
        cabecera.setFixedHeight(ALTO_CABECERA)
        disposicion_cabecera = QHBoxLayout(cabecera)
        disposicion_cabecera.setContentsMargins(ESPACIADO.lg, 0, ESPACIADO.lg, 0)
        disposicion_cabecera.setSpacing(ESPACIADO.sm)
        icono_titulo = QLabel()
        icono_titulo.setPixmap(icono("warning", COLORES.rojo, 20).pixmap(20, 20))
        titulo = QLabel(TITULO)
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

        texto = QLabel(TEXTO_EXPLICATIVO)
        texto.setWordWrap(True)
        texto.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_subtitulo))

        cuerpo = QVBoxLayout()
        cuerpo.setContentsMargins(
            ESPACIADO.xl, ESPACIADO.lg, ESPACIADO.xl, ESPACIADO.lg
        )
        cuerpo.addWidget(texto)

        self.boton_cancelar = QPushButton("Cancelar")
        self.boton_cancelar.setProperty("variante", "secundario")
        self.boton_cancelar.clicked.connect(self.reject)

        self.boton_confirmar = QPushButton("Detener y cerrar")
        self.boton_confirmar.setProperty("variante", "primario")
        self.boton_confirmar.clicked.connect(self.accept)

        pie = QFrame()
        pie.setObjectName("pie_dialogo")
        disposicion_pie = QHBoxLayout(pie)
        disposicion_pie.setContentsMargins(
            ESPACIADO.md, ESPACIADO.sm, ESPACIADO.md, ESPACIADO.sm
        )
        disposicion_pie.setSpacing(ESPACIADO.sm)
        disposicion_pie.addStretch(1)
        disposicion_pie.addWidget(self.boton_cancelar)
        disposicion_pie.addWidget(self.boton_confirmar)

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(0)
        disposicion.addWidget(cabecera)
        disposicion.addLayout(cuerpo)
        disposicion.addWidget(pie)
