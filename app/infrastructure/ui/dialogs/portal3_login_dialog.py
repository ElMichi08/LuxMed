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
ALTO_CABECERA = 40
ALTO_PIE = 48
TITULO = "Inicia sesión en el Portal 3 para comenzar"
TEXTO_EXPLICATIVO = (
    "Se abrió una ventana del navegador. Ingresa tus credenciales en el Portal 3. "
    "Solo lo harás una vez: la sesión se usa para todo el lote y solo vive en la memoria "
    "de este equipo. LuxMed no captura ni guarda tus credenciales."
)
TEXTO_EXPLICATIVO_REPROCESO = (
    "Se abrió una ventana del navegador. Ingresa tus credenciales en el Portal 3. "
    "La sesión solo vive en la memoria de este equipo. LuxMed no captura ni guarda tus credenciales."
)
TEXTO_NOTA = "La campaña comenzará automáticamente al iniciar sesión."
TEXTO_ESPERA = "Esperando que inicies sesión…"


class Portal3LoginDialog(QDialog):
    def __init__(
        self, es_reproceso: bool = False, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(TITULO)
        self.setModal(True)
        self.setFixedWidth(ANCHO)

        cabecera = QFrame()
        cabecera.setObjectName("cabecera_dialogo")
        cabecera.setFixedHeight(ALTO_CABECERA)
        disposicion_cabecera = QHBoxLayout(cabecera)
        disposicion_cabecera.setContentsMargins(ESPACIADO.md, 0, ESPACIADO.md, 0)
        disposicion_cabecera.setSpacing(ESPACIADO.sm)
        icono_titulo = QLabel()
        icono_titulo.setPixmap(icono("open_in_new", COLORES.tinta, 16).pixmap(16, 16))
        titulo = QLabel(TITULO)
        titulo.setFont(
            QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base, TIPOGRAFIA.peso_bold)
        )
        titulo.setWordWrap(True)
        disposicion_cabecera.addWidget(icono_titulo)
        disposicion_cabecera.addWidget(titulo, 1)

        texto_explicativo = (
            TEXTO_EXPLICATIVO_REPROCESO if es_reproceso else TEXTO_EXPLICATIVO
        )
        texto = QLabel(texto_explicativo)
        texto.setWordWrap(True)
        texto.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base))

        caja_estado = QFrame()
        caja_estado.setObjectName("caja_estado_espera")
        disposicion_estado = QHBoxLayout(caja_estado)
        disposicion_estado.setContentsMargins(
            ESPACIADO.sm, ESPACIADO.sm, ESPACIADO.sm, ESPACIADO.sm
        )
        disposicion_estado.setSpacing(ESPACIADO.sm)
        punto = QFrame()
        punto.setFixedSize(10, 10)
        punto.setStyleSheet(
            f"background-color: {COLORES.indigo}; border-radius: 5px; border: none;"
        )
        self._etiqueta_estado = QLabel(TEXTO_ESPERA)
        self._etiqueta_estado.setFont(
            QFont(
                TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base, TIPOGRAFIA.peso_medio
            )
        )
        self._etiqueta_estado.setStyleSheet(f"color: {COLORES.indigo}; border: none;")
        disposicion_estado.addWidget(punto)
        disposicion_estado.addWidget(self._etiqueta_estado, 1)

        cuerpo = QVBoxLayout()
        cuerpo.setContentsMargins(
            ESPACIADO.xl, ESPACIADO.lg, ESPACIADO.xl, ESPACIADO.lg
        )
        cuerpo.setSpacing(ESPACIADO.md)
        cuerpo.addWidget(texto)
        cuerpo.addWidget(caja_estado)
        self._nota: QLabel | None = None
        if not es_reproceso:
            self._nota = QLabel(TEXTO_NOTA)
            self._nota.setWordWrap(True)
            self._nota.setFont(
                QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_etiqueta)
            )
            self._nota.setStyleSheet(f"color: {COLORES.tinta_sec};")
            cuerpo.addWidget(self._nota)

        self.boton_cancelar = QPushButton("Cancelar")
        self.boton_cancelar.setProperty("variante", "secundario")
        self.boton_cancelar.clicked.connect(self.reject)

        pie = QFrame()
        pie.setObjectName("pie_dialogo")
        pie.setFixedHeight(ALTO_PIE)
        disposicion_pie = QHBoxLayout(pie)
        disposicion_pie.setContentsMargins(ESPACIADO.md, 0, ESPACIADO.md, 0)
        disposicion_pie.addStretch(1)
        disposicion_pie.addWidget(self.boton_cancelar)

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(0)
        disposicion.addWidget(cabecera)
        disposicion.addLayout(cuerpo)
        disposicion.addWidget(pie)
