from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.infrastructure.ui.presenters.settings_presenter import SettingsPresenter
from app.infrastructure.ui.screens.settings_view import SettingsView
from tests.ui.fakes.ports import FakeOutputFolderSettings


class VistaSettingsFalsa:
    def __init__(self) -> None:
        self.carpeta_mostrada: Path | None = None

    def mostrar_carpeta(self, carpeta: Path) -> None:
        self.carpeta_mostrada = carpeta


def test_settings_presenter_carga_y_muestra() -> None:
    vista = VistaSettingsFalsa()
    ajustes = FakeOutputFolderSettings(Path("D:/LuxMed/salidas"))
    presenter = SettingsPresenter(vista, ajustes)

    presenter.cargar()

    assert vista.carpeta_mostrada == Path("D:/LuxMed/salidas")


def test_settings_presenter_cambiar_carpeta_persiste_y_muestra() -> None:
    vista = VistaSettingsFalsa()
    ajustes = FakeOutputFolderSettings(Path("D:/LuxMed/salidas"))
    presenter = SettingsPresenter(vista, ajustes)

    presenter.cambiar_carpeta(Path("D:/otra/carpeta"))

    assert ajustes.obtener() == Path("D:/otra/carpeta")
    assert vista.carpeta_mostrada == Path("D:/otra/carpeta")


def test_settings_view_muestra_carpeta_en_el_campo() -> None:
    vista = SettingsView()
    carpeta = Path("D:/LuxMed/salidas")

    vista.mostrar_carpeta(carpeta)

    assert vista._campo_carpeta.text() == str(carpeta)


def test_settings_view_campo_es_solo_lectura() -> None:
    vista = SettingsView()

    assert vista._campo_carpeta.isReadOnly()


def test_captura_settings_view(capturar: Callable[..., Path]) -> None:
    vista = SettingsView()
    vista.mostrar_carpeta(Path("D:/LuxMed/salidas"))
    ruta = capturar(vista, "settings_view")
    assert ruta.exists()
