from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame

from app.infrastructure.ui.theme.logo import pixmap_logo
from app.infrastructure.ui.theme.tokens import GEOMETRIA
from app.infrastructure.ui.widgets.base import etiqueta, fila, separador_vertical
from app.infrastructure.ui.widgets.chip import StatusChip

TEXTO_SIN_LOTE = "Sin lote activo"
LADO_MONOGRAMA = 24


def iniciales(usuario: str) -> str:
    partes = [parte for parte in usuario.replace("_", ".").split(".") if parte]
    letras = "".join(parte[0] for parte in partes[:2]) or "?"
    return letras.upper()


class TopBar(QFrame):
    def __init__(self, usuario: str) -> None:
        super().__init__()
        self.setObjectName("barra_superior")
        self.setFixedHeight(GEOMETRIA.barra_superior)
        monograma = etiqueta()
        monograma.setPixmap(pixmap_logo(LADO_MONOGRAMA, self.devicePixelRatioF()))
        monograma.setFixedSize(LADO_MONOGRAMA, LADO_MONOGRAMA)
        self._contexto = etiqueta(TEXTO_SIN_LOTE, "mono")
        self._chip = StatusChip()
        self._chip.hide()
        avatar = etiqueta(iniciales(usuario), objeto="avatar")
        avatar.setFixedSize(28, 28)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout = fila((12, 0, 12, 0), 12)
        layout.addWidget(monograma)
        layout.addWidget(etiqueta("LuxMed", objeto="marca"))
        layout.addWidget(separador_vertical())
        layout.addWidget(self._contexto)
        layout.addWidget(self._chip)
        layout.addStretch(1)
        layout.addWidget(etiqueta(usuario, "mono"))
        layout.addWidget(avatar)
        self.setLayout(layout)

    def mostrar_lote(self, archivo: str, lote_id: str, filas: int) -> None:
        self._contexto.setText(f"{archivo} · Lote {lote_id} · {filas} filas")

    def mostrar_estado(self, texto: str, tono: str) -> None:
        self._chip.establecer(texto, tono)
        self._chip.show()

    def limpiar(self) -> None:
        self._contexto.setText(TEXTO_SIN_LOTE)
        self._chip.hide()
