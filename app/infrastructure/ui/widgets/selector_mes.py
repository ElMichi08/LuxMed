from __future__ import annotations

from collections.abc import Sequence

from PyQt6.QtWidgets import QComboBox

from app.application.mes_atencion import ConteoMes, MesAtencion, meses_recientes
from app.infrastructure.ui.theme.tokens import GEOMETRIA

MESES_RECIENTES = 6
ANCHO_SELECTOR = 220


class SelectorMes(QComboBox):
    def __init__(self) -> None:
        super().__init__()
        self.setFixedSize(ANCHO_SELECTOR, GEOMETRIA.boton)
        self.setToolTip("Carpeta dentro de la carpeta de salida donde se guardarán los entregables")

    @property
    def mes(self) -> MesAtencion | None:
        valor = self.currentData()
        return valor if isinstance(valor, MesAtencion) else None

    def establecer_opciones(self, encontrados: Sequence[ConteoMes], actual: MesAtencion) -> None:
        self.clear()
        for conteo in encontrados:
            self.addItem(f"{conteo.mes.nombre_carpeta} · {conteo.filas} filas", conteo.mes)
        ya_listados = {conteo.mes for conteo in encontrados}
        for mes in meses_recientes(actual.anterior(), MESES_RECIENTES):
            if mes not in ya_listados:
                self.addItem(mes.nombre_carpeta, mes)
        self.setCurrentIndex(0)
