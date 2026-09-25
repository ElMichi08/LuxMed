from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.application.lote_service import (
    ErrorPrecondicion,
    ServicioLote,
    motivo_descarte,
)
from app.application.progreso import AvancePaciente, ResumenLote
from app.application.validator import ValidatorService
from app.domain.entities import CredencialesPortal3, EstadoPaciente
from app.infrastructure.excel.excel_handler import ExcelHandler

EXCEL_REAL = Path(__file__).resolve().parents[1] / "docs" / "data" / "BASE.xlsx"


def _configuracion(carpeta: Path, credenciales: CredencialesPortal3) -> MagicMock:
    configuracion = MagicMock()
    configuracion.obtener_carpeta_salida.return_value = str(carpeta)
    configuracion.obtener_credenciales_portal3.return_value = credenciales
    return configuracion


def _servicio(tmp_path: Path, credenciales: CredencialesPortal3, fabrica: MagicMock | None = None) -> ServicioLote:
    return ServicioLote(
        ExcelHandler(),
        MagicMock(),
        ValidatorService(),
        _configuracion(tmp_path, credenciales),
        fabrica or MagicMock(),
    )


@pytest.mark.parametrize(
    ("cedula", "motivo"),
    [("17124981", "Cédula con 8 dígitos"), ("080129381A", "Cédula con caracteres no numéricos"), ("nan", "Cédula vacía")],
)
def test_motivo_descarte(cedula: str, motivo: str) -> None:
    assert motivo_descarte(cedula) == motivo


@pytest.mark.skipif(not EXCEL_REAL.is_file(), reason="Falta docs/data/BASE.xlsx")
def test_cargar_listado_real(tmp_path: Path) -> None:
    revision = _servicio(tmp_path, CredencialesPortal3("u", "p")).cargar_listado(str(EXCEL_REAL))
    assert len(revision.filas) == 6
    assert all(fila.es_valida for fila in revision.filas)
    assert all(fila.fecha_nacimiento is not None and fila.fecha_nacimiento.year > 1900 for fila in revision.filas)
    assert revision.filas[0].fila_excel == 2
    assert revision.lote_id.endswith("-01")


@pytest.mark.skipif(not EXCEL_REAL.is_file(), reason="Falta docs/data/BASE.xlsx")
def test_ejecutar_exige_credenciales(tmp_path: Path) -> None:
    servicio = _servicio(tmp_path, CredencialesPortal3("", ""))
    revision = servicio.cargar_listado(str(EXCEL_REAL))
    with pytest.raises(ErrorPrecondicion):
        servicio.ejecutar(revision, MagicMock())


@pytest.mark.skipif(not EXCEL_REAL.is_file(), reason="Falta docs/data/BASE.xlsx")
def test_ejecutar_usa_credenciales_vigentes_y_completa_resumen(tmp_path: Path) -> None:
    credenciales = CredencialesPortal3("medico", "clave")
    orquestador = MagicMock()
    orquestador.procesar_pacientes.side_effect = lambda cola, _obs: ResumenLote(
        inicio=MagicMock(), fin=MagicMock(), resultados=(AvancePaciente(cola[0][0], EstadoPaciente.COMPLETADO),)
    )
    fabrica = MagicMock(return_value=orquestador)
    servicio = _servicio(tmp_path, credenciales, fabrica)
    revision = servicio.cargar_listado(str(EXCEL_REAL))
    resumen = servicio.ejecutar(revision, MagicMock())
    credenciales_usadas, carpeta_pdfs = fabrica.call_args.args
    assert credenciales_usadas == credenciales
    assert carpeta_pdfs.endswith("pdfs")
    assert resumen.total == 6
    assert resumen.contar(EstadoPaciente.COMPLETADO) == 1
    assert resumen.contar(EstadoPaciente.PENDIENTE) == 5
