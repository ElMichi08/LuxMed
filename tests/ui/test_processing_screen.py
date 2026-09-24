from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from app.application.dto import (
    CabeceraLote,
    EstadoPaciente,
    LineaBitacora,
    Portal,
)
from app.infrastructure.ui.models.batch_filter_proxy import FiltroEstado
from app.infrastructure.ui.presenters.processing_presenter import ProcessingPresenter
from app.infrastructure.ui.screens.processing_view import ProcessingView
from tests.ui.fakes.dataset import (
    cabecera_simulada,
    filas_paciente_simuladas,
    progreso_simulado,
)


class VistaProcessingFalsa:
    def __init__(self) -> None:
        self.cabecera: CabeceraLote | None = None
        self.filas: tuple[object, ...] = ()
        self.progresos: list[object] = []

    def establecer_cabecera(self, cabecera: CabeceraLote) -> None:
        self.cabecera = cabecera

    def establecer_filas(self, filas: tuple[object, ...]) -> None:
        self.filas = filas

    def actualizar_progreso(self, progreso: object) -> None:
        self.progresos.append(progreso)

    def aplicar_actualizaciones(self, filas: tuple[object, ...]) -> None: ...
    def agregar_linea_bitacora(self, linea: object) -> None: ...
    def mostrar_solicitud_login_portal3(self, es_reproceso: bool = False) -> None: ...
    def ocultar_solicitud_login_portal3(self) -> None: ...
    def mostrar_solicitud_captcha(self, solicitud: object) -> None: ...
    def ocultar_solicitud_captcha(self) -> None: ...
    def mostrar_lote_detenido(self, resultado: object) -> None: ...
    def ocultar_lote_detenido(self) -> None: ...


def test_processing_presenter_puebla_la_vista_al_construirse() -> None:
    vista = VistaProcessingFalsa()
    cabecera = cabecera_simulada()
    filas = filas_paciente_simuladas()
    progreso = progreso_simulado()

    ProcessingPresenter(vista, cabecera, filas, progreso)

    assert vista.cabecera == cabecera
    assert len(vista.filas) == len(filas)
    assert vista.progresos == [progreso]


def test_batch_table_model_refleja_las_filas() -> None:
    vista = ProcessingView()
    vista.establecer_filas(filas_paciente_simuladas())
    assert vista._modelo.rowCount() == len(filas_paciente_simuladas())


def test_batch_table_model_apply_updates_actualiza_fila_existente() -> None:
    vista = ProcessingView()
    filas = filas_paciente_simuladas()
    vista.establecer_filas(filas)
    primera = filas[0]
    actualizada = primera.__class__(
        paciente_id=primera.paciente_id,
        nombre=primera.nombre,
        cedula=primera.cedula,
        edad=primera.edad,
        rama=primera.rama,
        seguro_derivado=primera.seguro_derivado,
        ruta=primera.ruta,
        estado=EstadoPaciente.EN_PROCESO,
        hora=primera.hora,
    )
    vista._modelo.apply_updates((actualizada,))
    assert vista._modelo.fila_en(0).estado is EstadoPaciente.EN_PROCESO


def test_processing_view_aplicar_actualizaciones_delega_en_el_modelo() -> None:
    vista = ProcessingView()
    filas = filas_paciente_simuladas()
    vista.establecer_filas(filas)
    primera = filas[0]
    actualizada = primera.__class__(
        paciente_id=primera.paciente_id,
        nombre=primera.nombre,
        cedula=primera.cedula,
        edad=primera.edad,
        rama=primera.rama,
        seguro_derivado=primera.seguro_derivado,
        ruta=primera.ruta,
        estado=EstadoPaciente.ERROR_PORTAL_3,
        hora=primera.hora,
    )

    vista.aplicar_actualizaciones((actualizada,))

    assert vista._modelo.fila_en(0).estado is EstadoPaciente.ERROR_PORTAL_3
    assert vista._modelo.rowCount() == len(filas)


def test_processing_view_agrega_linea_de_bitacora_con_portal() -> None:
    vista = ProcessingView()
    linea = LineaBitacora(
        hora=datetime(2026, 9, 8, 14, 18, 22),
        portal=Portal.P1,
        mensaje="consulta completada",
    )

    vista.agregar_linea_bitacora(linea)

    assert (
        vista._bitacora._ultima_linea.text()
        == "14:18:22 Portal 1 · consulta completada"
    )


def test_processing_view_agrega_linea_de_bitacora_sin_portal() -> None:
    vista = ProcessingView()
    linea = LineaBitacora(
        hora=datetime(2026, 9, 8, 14, 18, 22), portal=None, mensaje="lote iniciado"
    )

    vista.agregar_linea_bitacora(linea)

    assert vista._bitacora._ultima_linea.text() == "14:18:22 lote iniciado"


def test_processing_view_login_portal3_primera_vez_muestra_nota_de_campana() -> None:
    vista = ProcessingView()

    vista.mostrar_solicitud_login_portal3()

    assert vista._dialogo_login is not None
    assert vista._dialogo_login._nota is not None


def test_processing_view_login_portal3_reproceso_omite_nota_de_campana() -> None:
    vista = ProcessingView()

    vista.mostrar_solicitud_login_portal3(es_reproceso=True)

    assert vista._dialogo_login is not None
    assert vista._dialogo_login._nota is None


def test_filtro_segmentado_reduce_filas_visibles() -> None:
    vista = ProcessingView()
    vista.establecer_filas(filas_paciente_simuladas())
    total_sin_filtro = vista._proxy.rowCount()
    vista._proxy.establecer_filtro_estado(FiltroEstado.CON_ERROR)
    assert 0 < vista._proxy.rowCount() < total_sin_filtro


def test_captura_processing_con_datos(capturar: Callable[..., Path]) -> None:
    vista = ProcessingView()
    ProcessingPresenter(
        vista, cabecera_simulada(), filas_paciente_simuladas(), progreso_simulado()
    )
    ruta = capturar(vista, "processing_con_datos")
    assert ruta.exists()


def test_captura_processing_filtro_con_error(capturar: Callable[..., Path]) -> None:
    vista = ProcessingView()
    ProcessingPresenter(
        vista, cabecera_simulada(), filas_paciente_simuladas(), progreso_simulado()
    )
    vista._botones_filtro[FiltroEstado.CON_ERROR].setChecked(True)
    ruta = capturar(vista, "processing_filtro_con_error")
    assert ruta.exists()
