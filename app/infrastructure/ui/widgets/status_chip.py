from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QLabel, QWidget

from app.application.dto import EstadoPaciente
from app.infrastructure.ui.theme.stylesheet import repolish
from app.infrastructure.ui.theme.tokens import TIPOGRAFIA

TONO_POR_ESTADO: dict[EstadoPaciente, str] = {
    EstadoPaciente.COMPLETADO: "exito",
    EstadoPaciente.EN_PROCESO: "proceso",
    EstadoPaciente.PENDIENTE: "neutro",
    EstadoPaciente.CEDULA_INVALIDA: "alerta",
    EstadoPaciente.NO_ENCONTRADO: "alerta",
    EstadoPaciente.ERROR_PORTAL_1: "alerta",
    EstadoPaciente.ERROR_PORTAL_2: "alerta",
    EstadoPaciente.ERROR_PORTAL_3: "alerta",
}


class StatusChip(QLabel):
    def __init__(
        self, estado: EstadoPaciente | None = None, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setFont(
            QFont(
                TIPOGRAFIA.familia_mono,
                TIPOGRAFIA.tamano_chip,
                TIPOGRAFIA.peso_semibold,
            )
        )
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if estado is not None:
            self.establecer_estado(estado)

    def establecer_estado(self, estado: EstadoPaciente) -> None:
        self.setText(estado.value)
        self.setProperty("tono", TONO_POR_ESTADO[estado])
        repolish(self)
