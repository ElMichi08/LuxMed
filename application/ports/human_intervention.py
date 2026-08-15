from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol, runtime_checkable


class TipoIntervencion(Enum):
    ALTCHA_PORTAL_2 = "ALTCHA_PORTAL_2"
    PDF_CORRUPTO_PORTAL_2 = "PDF_CORRUPTO_PORTAL_2"
    # Portal 3 es candidato a repetir este patrón (docs/arquitectura.md), pero su
    # comportamiento sigue @pendiente en docs/BDD/06_consulta_portal3.feature — no se
    # agrega un valor aquí hasta confirmarlo.


@dataclass(frozen=True)
class SolicitudIntervencion:
    tipo: TipoIntervencion
    cedula_paciente: str
    mensaje: str
    opciones: tuple[str, ...]


@dataclass(frozen=True)
class ResolucionIntervencion:
    opcion_elegida: str
    valor: str | None = None  # ej. la cédula del titular escrita a mano


@runtime_checkable
class HumanInterventionPort(Protocol):
    """docs/arquitectura.md, sección "Contrato de human_intervention.py".

    El adapter de infraestructura (ej. portal2_adapter.py) agota sus reintentos
    internos y, si sigue fallando, invoca solicitar() con un objeto que describe qué se
    necesita. El puerto bloquea el worker thread hasta recibir una respuesta — implica
    una señal thread-safe entre el worker y el hilo de la GUI, disparada por los
    eventos de dominio HumanInterventionRequested / HumanInterventionResolved
    (mecanismo concreto todavía sin resolver, ver "Pendiente" en docs/arquitectura.md).
    La GUI implementa este puerto con un diálogo modal; el CLI de soporte, con un
    prompt de terminal — ninguno de los dos decide, solo recogen la respuesta del
    médico y se la devuelven al puerto.
    """

    def solicitar(self, solicitud: SolicitudIntervencion) -> ResolucionIntervencion: ...
