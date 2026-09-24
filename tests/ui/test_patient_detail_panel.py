from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.application.dto import DetallePaciente, EstadoPaciente
from app.infrastructure.ui.presenters.patient_detail_presenter import (
    PatientDetailPresenter,
)
from app.infrastructure.ui.screens.patient_detail_panel import PatientDetailPanel
from app.infrastructure.ui.screens.processing_view import ProcessingView
from tests.ui.fakes.dataset import (
    PACIENTES_SIMULADOS,
    detalle_simulado,
    filas_paciente_simuladas,
)
from tests.ui.fakes.ports import FakePatientDetailQuery


class VistaDetalleFalsa:
    def __init__(self) -> None:
        self.detalles_mostrados: list[DetallePaciente] = []

    def mostrar_detalle(self, detalle: DetallePaciente) -> None:
        self.detalles_mostrados.append(detalle)

    def limpiar(self) -> None: ...


def _id_con_estado(estado: EstadoPaciente) -> str:
    return next(p.paciente_id for p in PACIENTES_SIMULADOS if p.estado is estado)


def test_patient_detail_presenter_consulta_y_muestra() -> None:
    vista = VistaDetalleFalsa()
    presenter = PatientDetailPresenter(vista, FakePatientDetailQuery())

    paciente_id = _id_con_estado(EstadoPaciente.COMPLETADO)
    presenter.mostrar(paciente_id)

    assert len(vista.detalles_mostrados) == 1
    assert vista.detalles_mostrados[0].fila.paciente_id == paciente_id


def test_panel_muestra_completado_con_expediente() -> None:
    panel = PatientDetailPanel()
    paciente_id = _id_con_estado(EstadoPaciente.COMPLETADO)
    detalle = detalle_simulado(paciente_id)

    panel.mostrar_detalle(detalle)

    assert panel._nombre._texto_completo == detalle.fila.nombre
    assert panel._valor_cedula.text() == detalle.fila.cedula
    assert panel._boton_reprocesar.isEnabled() is False


def test_panel_habilita_reprocesar_para_error_portal() -> None:
    panel = PatientDetailPanel()
    paciente_id = _id_con_estado(EstadoPaciente.ERROR_PORTAL_3)
    detalle = detalle_simulado(paciente_id)

    panel.mostrar_detalle(detalle)

    assert panel._boton_reprocesar.isEnabled() is True


def test_panel_reprocesar_emite_paciente_id() -> None:
    panel = PatientDetailPanel()
    paciente_id = _id_con_estado(EstadoPaciente.ERROR_PORTAL_3)
    panel.mostrar_detalle(detalle_simulado(paciente_id))

    emitidos: list[str] = []
    panel.reproceso_solicitado.connect(emitidos.append)
    panel._boton_reprocesar.click()

    assert emitidos == [paciente_id]


def test_panel_limpiar_deshabilita_reprocesar() -> None:
    panel = PatientDetailPanel()
    panel.mostrar_detalle(
        detalle_simulado(_id_con_estado(EstadoPaciente.ERROR_PORTAL_3))
    )

    panel.limpiar()

    assert panel._boton_reprocesar.isEnabled() is False
    assert panel._nombre.text() == ""


def test_seleccionar_fila_en_tabla_emite_paciente_seleccionado() -> None:
    vista = ProcessingView()
    vista.establecer_filas(filas_paciente_simuladas())

    emitidos: list[str] = []
    vista.paciente_seleccionado.connect(emitidos.append)

    indice = vista._proxy.index(0, 0)
    seleccion = vista._tabla.selectionModel()
    assert seleccion is not None
    seleccion.select(
        indice,
        seleccion.SelectionFlag.Select | seleccion.SelectionFlag.Rows,
    )

    assert len(emitidos) == 1
    assert not vista.panel_detalle.isHidden()


def test_captura_processing_con_detalle_seleccionado(
    capturar: Callable[..., Path],
) -> None:
    vista = ProcessingView()
    vista.establecer_filas(filas_paciente_simuladas())
    paciente_id = _id_con_estado(EstadoPaciente.COMPLETADO)
    presenter = PatientDetailPresenter(vista.panel_detalle, FakePatientDetailQuery())
    vista.paciente_seleccionado.connect(presenter.mostrar)

    indice_modelo = next(
        indice
        for indice, p in enumerate(filas_paciente_simuladas())
        if p.paciente_id == paciente_id
    )
    indice_proxy = vista._proxy.mapFromSource(vista._modelo.index(indice_modelo, 0))
    seleccion = vista._tabla.selectionModel()
    assert seleccion is not None
    seleccion.select(
        indice_proxy, seleccion.SelectionFlag.Select | seleccion.SelectionFlag.Rows
    )

    ruta = capturar(vista, "processing_con_detalle", 1600, 800)
    assert ruta.exists()
