from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace
from datetime import datetime, time, timedelta

from app.domain.entities import (
    EntidadSeguro,
    EstadoPaciente,
    EstadoPaso,
    EstadoValidacion,
    Paciente,
    Portal,
    Rama,
)

ESTADOS_FINALES = frozenset(
    {
        EstadoPaciente.COMPLETADO,
        EstadoPaciente.CEDULA_INVALIDA,
        EstadoPaciente.NO_ENCONTRADO,
        EstadoPaciente.ERROR_PORTAL_1,
        EstadoPaciente.ERROR_PORTAL_2,
        EstadoPaciente.ERROR_PORTAL_3,
    }
)

ERROR_POR_PORTAL = {
    Portal.P1: EstadoPaciente.ERROR_PORTAL_1,
    Portal.P2: EstadoPaciente.ERROR_PORTAL_2,
    Portal.P3: EstadoPaciente.ERROR_PORTAL_3,
}


def rama_de(entidad: EntidadSeguro) -> Rama:
    if entidad is EntidadSeguro.IESS:
        return Rama.A
    if entidad in (EntidadSeguro.ISSFA, EntidadSeguro.ISSPOL):
        return Rama.B
    return Rama.SIN_RAMA


@dataclass(frozen=True, slots=True)
class PasosRuta:
    p1: EstadoPaso = EstadoPaso.PENDIENTE
    p2: EstadoPaso = EstadoPaso.PENDIENTE
    p3: EstadoPaso = EstadoPaso.PENDIENTE

    def de(self, portal: Portal) -> EstadoPaso:
        return {Portal.P1: self.p1, Portal.P2: self.p2, Portal.P3: self.p3}[portal]

    def con(self, portal: Portal, estado: EstadoPaso) -> PasosRuta:
        return replace(self, **{portal.value.lower(): estado})

    def como_tupla(self) -> tuple[EstadoPaso, EstadoPaso, EstadoPaso]:
        return (self.p1, self.p2, self.p3)


@dataclass(frozen=True, slots=True)
class AvancePaciente:
    indice: int
    estado: EstadoPaciente
    rama: Rama = Rama.SIN_RAMA
    seguro_derivado: bool | None = None
    pasos: PasosRuta = field(default_factory=PasosRuta)
    hora: time | None = None
    portal_actual: Portal | None = None

    @property
    def es_final(self) -> bool:
        return self.estado in ESTADOS_FINALES


@dataclass(frozen=True, slots=True)
class ResumenLote:
    inicio: datetime
    fin: datetime
    resultados: tuple[AvancePaciente, ...]
    detenido: bool = False

    @property
    def duracion(self) -> timedelta:
        return self.fin - self.inicio

    @property
    def total(self) -> int:
        return len(self.resultados)

    def contar(self, estado: EstadoPaciente, rama: Rama | None = None) -> int:
        return sum(
            1
            for resultado in self.resultados
            if resultado.estado is estado and (rama is None or resultado.rama is rama)
        )

    def contar_rama(self, rama: Rama) -> int:
        return sum(1 for resultado in self.resultados if resultado.rama is rama)

    @property
    def filas_en_rojo(self) -> int:
        return sum(
            1 for resultado in self.resultados if resultado.estado is not EstadoPaciente.COMPLETADO
        )


class IObservadorLote(ABC):
    @abstractmethod
    def paciente_actualizado(self, avance: AvancePaciente) -> None: pass

    @abstractmethod
    def detencion_solicitada(self) -> bool: pass


class ObservadorNulo(IObservadorLote):
    def paciente_actualizado(self, avance: AvancePaciente) -> None:
        return None

    def detencion_solicitada(self) -> bool:
        return False


class RastreadorPaciente:
    def __init__(self, indice: int, observador: IObservadorLote) -> None:
        self._observador = observador
        self._avance = AvancePaciente(indice=indice, estado=EstadoPaciente.PENDIENTE)
        self._no_encontrado = False

    @property
    def avance(self) -> AvancePaciente:
        return self._avance

    def iniciar(self, portal: Portal) -> None:
        self._actualizar(
            estado=EstadoPaciente.EN_PROCESO,
            pasos=self._avance.pasos.con(portal, EstadoPaso.EN_CURSO),
            portal_actual=portal,
        )

    def terminar(self, portal: Portal, exito: bool) -> None:
        resultado = EstadoPaso.HECHO if exito else EstadoPaso.FALLIDO
        self._actualizar(pasos=self._avance.pasos.con(portal, resultado), portal_actual=None)

    def omitir(self, portal: Portal) -> None:
        self._actualizar(pasos=self._avance.pasos.con(portal, EstadoPaso.OMITIDO))

    def fallo_en_curso(self) -> None:
        portal = self._avance.portal_actual
        if portal is not None:
            self.terminar(portal, exito=False)

    def marcar_no_encontrado(self) -> None:
        self._no_encontrado = True
        self.terminar(Portal.P1, exito=False)

    def clasificar(self, paciente: Paciente) -> None:
        self._actualizar(
            rama=rama_de(paciente.entidad_detectada),
            seguro_derivado=(
                paciente.seguro_derivado if paciente.entidad_detectada is EntidadSeguro.IESS else None
            ),
        )

    def resolver(self, paciente: Paciente) -> AvancePaciente:
        estado = self._estado_final(paciente)
        paciente.es_auditoria_rojo = estado is not EstadoPaciente.COMPLETADO
        self._actualizar(estado=estado, portal_actual=None, hora=datetime.now().time())
        return self._avance

    def _estado_final(self, paciente: Paciente) -> EstadoPaciente:
        if self._no_encontrado:
            return EstadoPaciente.NO_ENCONTRADO
        for portal in Portal:
            if self._avance.pasos.de(portal) is EstadoPaso.FALLIDO:
                return ERROR_POR_PORTAL[portal]
        if paciente.estado is not EstadoValidacion.VALIDO:
            return EstadoPaciente.ERROR_PORTAL_1
        if paciente.pdf_p1_propio_bytes is None:
            return EstadoPaciente.ERROR_PORTAL_1
        if paciente.seguro_derivado and paciente.pdf_p1_acreditador_bytes is None:
            return EstadoPaciente.ERROR_PORTAL_1
        if paciente.pdf_p3_bytes is None:
            return EstadoPaciente.ERROR_PORTAL_3
        return EstadoPaciente.COMPLETADO

    def _actualizar(self, **cambios: object) -> None:
        self._avance = replace(self._avance, **cambios)
        self._observador.paciente_actualizado(self._avance)
