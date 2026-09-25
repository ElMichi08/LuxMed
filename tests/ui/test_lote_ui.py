from __future__ import annotations

import threading
from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton
from pytestqt.qtbot import QtBot

from app.application.lote_service import FilaRevision, RevisionLote
from app.application.progreso import AvancePaciente, IObservadorLote, ResumenLote
from app.domain.entities import CredencialesPortal3, EstadoPaciente, Paciente
from app.infrastructure.ui.guards import AccionUnica
from app.infrastructure.ui.log_bridge import EmisorLog
from app.infrastructure.ui.models.columnas import Columna, ModeloColumnas
from app.infrastructure.ui.models.filtro_proxy import FiltroProxy
from app.infrastructure.ui.privacidad_logs import SanitizadorPii
from app.infrastructure.ui.shell.lote_controller import LoteController
from app.infrastructure.ui.shell.main_window import MainWindow, PaginaLote


def _revision() -> RevisionLote:
    filas = (
        FilaRevision(0, 2, "ANA PEREZ", "0102030405", date(1990, 1, 1), 36, "IESS", "CENTRO", None),
        FilaRevision(1, 3, "LUIS MORA", "123", None, None, "IESS", "CENTRO", "Cédula con 3 dígitos"),
    )
    pacientes = tuple(
        Paciente(fila.nombre, fila.cedula, date(1990, 1, 1), fila.seguro, date(2026, 4, 1), fila.establecimiento)
        for fila in filas
    )
    return RevisionLote("2026-09-24-01", "BASE.xlsx", filas, pacientes)


def test_accion_unica_ignora_reentrada(qtbot: QtBot) -> None:
    boton = QPushButton("Iniciar campaña")
    qtbot.addWidget(boton)
    accion = AccionUnica([boton], "Iniciando…")
    assert accion.intentar() is True
    assert accion.intentar() is False
    assert not boton.isEnabled()
    assert boton.text() == "Iniciando…"
    accion.liberar()
    assert boton.isEnabled()
    assert boton.text() == "Iniciar campaña"


def test_accion_deshabilitada_no_se_ejecuta(qtbot: QtBot) -> None:
    boton = QPushButton("Generar")
    qtbot.addWidget(boton)
    accion = AccionUnica([boton], "Generando…")
    accion.establecer_habilitada(False)
    assert accion.intentar() is False
    assert not boton.isEnabled()


def test_proxy_filtra_por_predicado_y_texto(qtbot: QtBot) -> None:
    modelo = ModeloColumnas([Columna("Nombre", str)])
    modelo.establecer_filas(["ana 0102", "luis 0999", "maria 0102"])
    proxy = FiltroProxy(str)
    proxy.setSourceModel(modelo)
    proxy.establecer_texto("0102")
    assert proxy.rowCount() == 2
    proxy.establecer_predicado(lambda fila: str(fila).startswith("m"))
    assert proxy.rowCount() == 1


def test_doble_clic_en_iniciar_campana_lanza_un_solo_lote(qtbot: QtBot, tmp_path: Path) -> None:
    liberar = threading.Event()
    llamadas: list[int] = []

    def ejecutar(revision: RevisionLote, observador: IObservadorLote, mes: object) -> ResumenLote:
        llamadas.append(1)
        observador.paciente_actualizado(AvancePaciente(0, EstadoPaciente.EN_PROCESO))
        liberar.wait(5)
        return ResumenLote(
            datetime.now(),
            datetime.now(),
            (AvancePaciente(0, EstadoPaciente.COMPLETADO), AvancePaciente(1, EstadoPaciente.CEDULA_INVALIDA)),
        )

    servicio = MagicMock()
    servicio.ejecutar.side_effect = ejecutar
    configuracion = MagicMock()
    configuracion.obtener_carpeta_salida.return_value = str(tmp_path)
    configuracion.obtener_credenciales_portal3.return_value = CredencialesPortal3("u", "p")
    ventana = MainWindow("admision.01", "v-test")
    qtbot.addWidget(ventana)
    controlador = LoteController(servicio, configuracion, ventana, EmisorLog(), tmp_path / "logs", SanitizadorPii())
    controlador._listado_cargado(_revision())
    assert ventana.pagina_lote is PaginaLote.REVISION

    boton = ventana.review.boton_iniciar
    qtbot.mouseClick(boton, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(boton, Qt.MouseButton.LeftButton)
    controlador._iniciar_campana()
    assert controlador.lote_en_curso
    assert not boton.isEnabled()

    liberar.set()
    qtbot.waitUntil(lambda: not controlador.lote_en_curso, timeout=5000)
    assert len(llamadas) == 1
    assert ventana.pagina_lote is PaginaLote.RESUMEN
    assert ventana.summary.boton_entregables.isEnabled()


def test_iniciar_sin_credenciales_no_lanza_hilo(qtbot: QtBot, tmp_path: Path, monkeypatch) -> None:
    from app.application.lote_service import ErrorPrecondicion
    from app.infrastructure.ui.shell import lote_controller

    servicio = MagicMock()
    servicio.verificar_precondiciones.side_effect = ErrorPrecondicion("Faltan credenciales")
    configuracion = MagicMock()
    configuracion.obtener_carpeta_salida.return_value = str(tmp_path)
    configuracion.obtener_credenciales_portal3.return_value = CredencialesPortal3("", "")
    ventana = MainWindow("admision.01", "v-test")
    qtbot.addWidget(ventana)
    controlador = LoteController(servicio, configuracion, ventana, EmisorLog(), tmp_path / "logs", SanitizadorPii())
    avisos: list[str] = []
    monkeypatch.setattr(controlador, "_avisar_precondicion", avisos.append)
    controlador._listado_cargado(_revision())
    controlador._iniciar_campana()
    assert avisos == ["Faltan credenciales"]
    assert not controlador.lote_en_curso
    assert ventana.review.boton_iniciar.isEnabled()
    servicio.ejecutar.assert_not_called()
    assert lote_controller is not None
