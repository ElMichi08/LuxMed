from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PyQt6.QtCore import Qt

from app.application.dto import FilaError
from app.infrastructure.ui.presenters.errors_presenter import ErrorsPresenter
from app.infrastructure.ui.screens.errors_view import ErrorsView
from tests.ui.fakes.dataset import errores_simulados
from tests.ui.fakes.ports import FakeErrorListQuery


class VistaErrorsFalsa:
    def __init__(self) -> None:
        self.errores_mostrados: tuple[FilaError, ...] | None = None

    def mostrar_errores(self, errores: tuple[FilaError, ...]) -> None:
        self.errores_mostrados = errores


def test_errors_presenter_carga_y_muestra() -> None:
    vista = VistaErrorsFalsa()
    presenter = ErrorsPresenter(vista, FakeErrorListQuery())

    presenter.cargar()

    assert vista.errores_mostrados == errores_simulados()


def test_errors_view_todos_seleccionados_por_defecto() -> None:
    vista = ErrorsView()
    vista.mostrar_errores(errores_simulados())

    assert vista._modelo.total_seleccionados() == len(errores_simulados())
    assert "4 de 4 pacientes seleccionados" in vista._etiqueta_seleccion.text()


def test_errors_view_desmarcar_actualiza_pie() -> None:
    vista = ErrorsView()
    vista.mostrar_errores(errores_simulados())
    indice = vista._modelo.index(0, 0)

    vista._modelo.setData(
        indice, Qt.CheckState.Unchecked.value, Qt.ItemDataRole.CheckStateRole
    )

    assert vista._modelo.total_seleccionados() == 3
    assert "3 de 4 pacientes seleccionados" in vista._etiqueta_seleccion.text()


def test_errors_view_reintentar_emite_ids_seleccionados() -> None:
    vista = ErrorsView()
    vista.mostrar_errores(errores_simulados())
    indice = vista._modelo.index(0, 0)
    vista._modelo.setData(
        indice, Qt.CheckState.Unchecked.value, Qt.ItemDataRole.CheckStateRole
    )

    emitidos: list[tuple[str, ...]] = []
    vista.reproceso_solicitado.connect(emitidos.append)
    vista._boton_reintentar.click()

    assert len(emitidos) == 1
    assert len(emitidos[0]) == 3


def test_errors_view_boton_deshabilitado_sin_seleccion() -> None:
    vista = ErrorsView()
    vista.mostrar_errores(errores_simulados())
    for fila in range(vista._modelo.rowCount()):
        indice = vista._modelo.index(fila, 0)
        vista._modelo.setData(
            indice, Qt.CheckState.Unchecked.value, Qt.ItemDataRole.CheckStateRole
        )

    assert not vista._boton_reintentar.isEnabled()


def test_captura_errors_view(capturar: Callable[..., Path]) -> None:
    vista = ErrorsView()
    vista.mostrar_errores(errores_simulados())
    ruta = capturar(vista, "errors_view")
    assert ruta.exists()


def test_errors_view_sin_errores_muestra_estado_vacio() -> None:
    vista = ErrorsView()
    vista.show()

    vista.mostrar_errores(())

    assert vista._estado_vacio.isVisible()
    assert not vista._contenedor_tabla.isVisible()
    assert not vista._pie.isVisible()


def test_errors_view_con_errores_oculta_estado_vacio() -> None:
    vista = ErrorsView()
    vista.show()

    vista.mostrar_errores(errores_simulados())

    assert not vista._estado_vacio.isVisible()
    assert vista._contenedor_tabla.isVisible()
    assert vista._pie.isVisible()


def test_captura_errors_view_sin_errores(capturar: Callable[..., Path]) -> None:
    vista = ErrorsView()
    vista.mostrar_errores(())
    ruta = capturar(vista, "errors_view_vacio")
    assert ruta.exists()
