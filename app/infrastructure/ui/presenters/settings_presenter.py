from __future__ import annotations

from pathlib import Path

from app.application.ui_ports import IOutputFolderSettings
from app.infrastructure.ui.presenters.contracts import ISettingsView


class SettingsPresenter:
    def __init__(self, vista: ISettingsView, ajustes: IOutputFolderSettings) -> None:
        self._vista = vista
        self._ajustes = ajustes

    def cargar(self) -> None:
        self._vista.mostrar_carpeta(self._ajustes.obtener())

    def cambiar_carpeta(self, carpeta: Path) -> None:
        self._ajustes.guardar(carpeta)
        self._vista.mostrar_carpeta(carpeta)
