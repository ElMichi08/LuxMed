from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest

from app.application.orchestrator import OrchestratorService
from app.application.progreso import AvancePaciente, IObservadorLote
from app.domain.entities import EstadoPaciente, EstadoPaso, Paciente, Portal, Rama

PDF = b"%PDF-1.4 fake"


class ObservadorRegistro(IObservadorLote):
    def __init__(self, detener_tras: int | None = None) -> None:
        self.avances: list[AvancePaciente] = []
        self._detener_tras = detener_tras
        self.consultas = 0

    def paciente_actualizado(self, avance: AvancePaciente) -> None:
        self.avances.append(avance)

    def detencion_solicitada(self) -> bool:
        self.consultas += 1
        return self._detener_tras is not None and self.consultas > self._detener_tras


def _paciente(cedula: str = "0105556567") -> Paciente:
    return Paciente(
        nombre_y_apellidos="PACIENTE PRUEBA",
        cedula=cedula,
        fecha_nacimiento=date(1990, 1, 1),
        aporta="",
        fecha_atencion=date(2026, 4, 7),
        nom_establecimiento="HOSPITAL",
    )


def _orquestador(
    respuesta_p1: tuple[str, str, str, bytes | None] | Exception,
    acreditador: str | None | Exception = None,
    pdf_p3: bytes | None | Exception = PDF,
) -> OrchestratorService:
    scraper = MagicMock()
    scraper.procesar_portal_1.side_effect = (
        respuesta_p1 if isinstance(respuesta_p1, Exception) else lambda *_: respuesta_p1
    )
    scraper.extraer_acreditador_portal_2.side_effect = (
        acreditador if isinstance(acreditador, Exception) else lambda *_: acreditador
    )
    portal3 = MagicMock()
    portal3.procesar_portal_3.side_effect = pdf_p3 if isinstance(pdf_p3, Exception) else lambda *_: pdf_p3
    return OrchestratorService(repository=MagicMock(), scraper=scraper, portal3_adapter=portal3)


def _ejecutar(orquestador: OrchestratorService) -> tuple[AvancePaciente, ObservadorRegistro, Paciente]:
    observador = ObservadorRegistro()
    paciente = _paciente()
    resumen = orquestador.procesar_pacientes([(7, paciente)], observador)
    assert len(resumen.resultados) == 1
    return resumen.resultados[0], observador, paciente


IESS = ("IESS", "Seguro general", "si registra cobertura", PDF)
ISSFA = ("ISSFA", "Seguro ISSFA", "si registra cobertura", PDF)


def test_rama_a_sin_titular_completa() -> None:
    final, observador, paciente = _ejecutar(_orquestador(IESS))
    assert final.indice == 7
    assert final.estado is EstadoPaciente.COMPLETADO
    assert final.rama is Rama.A
    assert final.seguro_derivado is False
    assert final.pasos.como_tupla() == (EstadoPaso.HECHO,) * 3
    assert final.hora is not None
    assert paciente.es_auditoria_rojo is False
    assert any(avance.portal_actual is Portal.P2 for avance in observador.avances)


def test_rama_a_con_titular_marca_seguro_derivado() -> None:
    final, _observador, _paciente_final = _ejecutar(_orquestador(IESS, acreditador="0998887776"))
    assert final.estado is EstadoPaciente.COMPLETADO
    assert final.seguro_derivado is True


def test_rama_b_omite_portal_2() -> None:
    final, _observador, _paciente_final = _ejecutar(_orquestador(ISSFA))
    assert final.estado is EstadoPaciente.COMPLETADO
    assert final.rama is Rama.B
    assert final.seguro_derivado is None
    assert final.pasos.p2 is EstadoPaso.OMITIDO


def test_sin_cobertura_es_no_encontrado() -> None:
    final, _observador, paciente = _ejecutar(_orquestador(("", "", "No registra cobertura", None)))
    assert final.estado is EstadoPaciente.NO_ENCONTRADO
    assert final.rama is Rama.SIN_RAMA
    assert final.pasos.p1 is EstadoPaso.FALLIDO
    assert paciente.es_auditoria_rojo is True


@pytest.mark.parametrize(
    ("orquestador", "estado", "portal_fallido"),
    [
        (lambda: _orquestador(TimeoutError("p1")), EstadoPaciente.ERROR_PORTAL_1, "p1"),
        (lambda: _orquestador(IESS, acreditador=RuntimeError("altcha")), EstadoPaciente.ERROR_PORTAL_2, "p2"),
        (lambda: _orquestador(IESS, pdf_p3=None), EstadoPaciente.ERROR_PORTAL_3, "p3"),
        (lambda: _orquestador(ISSFA, pdf_p3=RuntimeError("p3")), EstadoPaciente.ERROR_PORTAL_3, "p3"),
    ],
)
def test_errores_por_portal(orquestador, estado: EstadoPaciente, portal_fallido: str) -> None:
    final, _observador, paciente = _ejecutar(orquestador())
    assert final.estado is estado
    assert getattr(final.pasos, portal_fallido) is EstadoPaso.FALLIDO
    assert paciente.es_auditoria_rojo is True


def test_pdf_de_portal_1_ausente_no_completa() -> None:
    final, _observador, _paciente_final = _ejecutar(
        _orquestador(("IESS", "Seguro general", "si registra cobertura", None))
    )
    assert final.estado is EstadoPaciente.ERROR_PORTAL_1


def test_detencion_entre_pacientes() -> None:
    orquestador = _orquestador(IESS)
    observador = ObservadorRegistro(detener_tras=1)
    resumen = orquestador.procesar_pacientes([(0, _paciente("0000000001")), (1, _paciente("0000000002"))], observador)
    assert resumen.detenido is True
    assert [avance.indice for avance in resumen.resultados] == [0]
