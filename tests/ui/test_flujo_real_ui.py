from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytestqt.qtbot import QtBot

from app.application.lote_service import ServicioLote
from app.application.validator import ValidatorService
from app.domain.entities import CredencialesPortal3
from app.infrastructure.excel.excel_handler import ExcelHandler
from app.infrastructure.ui.log_bridge import EmisorLog
from app.infrastructure.ui.privacidad_logs import SanitizadorPii
from app.infrastructure.ui.shell.lote_controller import LoteController
from app.infrastructure.ui.shell.main_window import MainWindow, PaginaLote

EXCEL_REAL = Path(__file__).resolve().parents[2] / "docs" / "data" / "BASE.xlsx"

pytestmark = pytest.mark.skipif(not EXCEL_REAL.is_file(), reason="Falta docs/data/BASE.xlsx")


def test_carga_real_y_entregables(qtbot: QtBot, tmp_path: Path) -> None:
    configuracion = MagicMock()
    configuracion.obtener_carpeta_salida.return_value = str(tmp_path)
    configuracion.obtener_credenciales_portal3.return_value = CredencialesPortal3("u", "p")
    servicio = ServicioLote(ExcelHandler(), MagicMock(), ValidatorService(), configuracion, MagicMock())
    ventana = MainWindow("admision.01", "v-test")
    qtbot.addWidget(ventana)
    controlador = LoteController(servicio, configuracion, ventana, EmisorLog(), tmp_path / "logs", SanitizadorPii())

    ventana.upload.dropzone.archivo_elegido.emit(str(EXCEL_REAL))
    ventana.upload.dropzone.archivo_elegido.emit(str(EXCEL_REAL))
    assert ventana.overlay.activo
    qtbot.waitUntil(lambda: ventana.pagina_lote is PaginaLote.REVISION, timeout=10000)
    assert not ventana.overlay.activo
    assert ventana.review.boton_iniciar.isEnabled()

    controlador._generar_entregables()
    qtbot.waitUntil(lambda: ventana.pagina_lote is PaginaLote.RESUMEN, timeout=10000)
    carpetas = list(tmp_path.glob("Lote_*"))
    assert len(carpetas) == 1
    assert (carpetas[0] / "BASE_limpio.xlsx").is_file()
    assert (carpetas[0] / "BASE_auditado.xlsx").is_file()
