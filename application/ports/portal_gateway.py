from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Protocol, runtime_checkable


class PortalTimeoutError(Exception):
    """El portal agotó sus reintentos internos por timeout persistente (backoff vive en
    el adapter, no aquí). process_patient.py la traduce al estado de error del portal
    correspondiente."""


@dataclass(frozen=True)
class ResultadoConsultaPortal1:
    encontrado: bool
    tipo_seguro: str | None = None
    es_menor_edad: bool | None = None
    pdf_path: Path | None = None


@runtime_checkable
class Portal1Gateway(Protocol):
    """docs/BDD/03_consulta_portal1.feature.

    Intercepta la respuesta de cobertura y descarga el PDF #1. Ante timeout, el adapter
    reintenta hasta 3 veces por su cuenta; si el fallo persiste, levanta
    PortalTimeoutError (se traduce a "ERROR_PORTAL_1" en application).
    """

    def consultar(self, cedula: str, fecha_atencion: date) -> ResultadoConsultaPortal1: ...


@dataclass(frozen=True)
class ResultadoConsultaPortal2:
    tiene_cobertura: bool
    pdf_path: Path | None = None  # None cuando tiene_cobertura es False (SIN_COBERTURA_PORTAL_2)


class ErrorPortal2(Exception):
    """El médico eligió marcar el paciente en error tras agotar el ciclo de ALTCHA (3
    intentos automáticos + intervención humana + decisión del médico)."""


class PdfCorruptoPortal2(Exception):
    """El médico revisó el PDF del titular y no pudo proporcionar su cédula tras el
    ciclo de reintento + intervención humana."""


@runtime_checkable
class Portal2Gateway(Protocol):
    """docs/BDD/05_consulta_portal2.feature. Solo se consulta en Rama A.

    consultar_titular() puede bloquear internamente vía el puerto human_intervention
    (ciclo de ALTCHA, ciclo de PDF corrupto) — es responsabilidad del adapter, no de
    quien llama a este puerto. El motivo de consulta es siempre "Enfermedad"
    (docs/BDD/01_normalizacion_excel.feature), por eso no es un parámetro: no hay
    variabilidad real que justifique exponerlo.
    """

    def consultar_titular(
        self, cedula: str, fecha_atencion: date
    ) -> ResultadoConsultaPortal2: ...


@dataclass(frozen=True)
class ResultadoConsultaPortal3:
    pdf_path: Path


class SesionPortal3ExpiradaError(Exception):
    """La sesión del Portal 3 expiró a mitad del lote (docs/BDD/08_pausa_reanudacion_lote.feature,
    escenario "Pausa forzada por expiración de sesión del Portal 3")."""


@runtime_checkable
class Portal3Gateway(Protocol):
    """docs/BDD/02_arranque_autenticacion_portal3.feature + 06_consulta_portal3.feature
    (solo sus 2 escenarios validados — ver advertencia abajo).

    iniciar_sesion() abre el navegador visible en el login del Portal 3 y bloquea hasta
    que el médico se autentica manualmente; el sistema nunca captura, recibe ni
    almacena esas credenciales (invariante #5). La sesión vive solo en memoria
    (contexto de navegador no persistente) y se reutiliza para todo el lote.

    ADVERTENCIA: el comportamiento de fallo de consultar_atencion() más allá de la
    expiración de sesión (timeout, reintentos, "ERROR_PORTAL_3") sigue @pendiente en
    docs/BDD/06_consulta_portal3.feature — no está modelado aquí todavía a propósito;
    este contrato puede ganar una excepción de timeout análoga a PortalTimeoutError
    cuando el propietario confirme ese comportamiento contra el portal real.
    """

    def iniciar_sesion(self) -> None: ...

    def consultar_atencion(
        self, cedula: str, fecha_atencion: date
    ) -> ResultadoConsultaPortal3: ...
