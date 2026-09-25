from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel

from app.infrastructure.ui.widgets.base import establecer_propiedad

ALTO_CHIP = 20


class StatusChip(QLabel):
    def __init__(self, texto: str = "", tono: str = "neutro") -> None:
        super().__init__(texto)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(ALTO_CHIP)
        self.establecer(texto, tono)

    def establecer(self, texto: str, tono: str) -> None:
        self.setText(texto)
        establecer_propiedad(self, "tono", tono)
