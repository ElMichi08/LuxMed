from __future__ import annotations

from collections.abc import Sequence

from PyQt6.QtCore import QObject
from PyQt6.QtWidgets import QAbstractButton, QWidget


class AccionUnica(QObject):
    def __init__(
        self,
        botones: Sequence[QAbstractButton],
        texto_ocupado: str,
        extras: Sequence[QWidget] = (),
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._botones = tuple(botones)
        self._extras = tuple(extras)
        self._textos = {boton: boton.text() for boton in self._botones}
        self._texto_ocupado = texto_ocupado
        self._ocupada = False
        self._habilitada = True

    @property
    def ocupada(self) -> bool:
        return self._ocupada

    def intentar(self) -> bool:
        if self._ocupada or not self._habilitada:
            return False
        self._ocupada = True
        for boton in self._botones:
            boton.setText(self._texto_ocupado)
        self._aplicar()
        return True

    def liberar(self) -> None:
        self._ocupada = False
        for boton, texto in self._textos.items():
            boton.setText(texto)
        self._aplicar()

    def establecer_habilitada(self, habilitada: bool) -> None:
        self._habilitada = habilitada
        self._aplicar()

    def _aplicar(self) -> None:
        activo = self._habilitada and not self._ocupada
        for widget in (*self._botones, *self._extras):
            widget.setEnabled(activo)
