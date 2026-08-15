from __future__ import annotations

from enum import Enum


class EstadoPaciente(Enum):
    PENDIENTE = "PENDIENTE"
    COMPLETADO = "COMPLETADO"
    NO_ENCONTRADO = "NO_ENCONTRADO"
    CEDULA_INVALIDA = "CEDULA_INVALIDA"
    ERROR_PORTAL_1 = "ERROR_PORTAL_1"
    SIN_COBERTURA_PORTAL_2 = "SIN_COBERTURA_PORTAL_2"
    ERROR_PORTAL_2 = "ERROR_PORTAL_2"
    PDF_CORRUPTO_PORTAL_2 = "PDF_CORRUPTO_PORTAL_2"
    # ERROR_PORTAL_3 deliberadamente omitido: sigue @pendiente en
    # docs/BDD/06_consulta_portal3.feature, sin confirmar por el propietario.


class EstadoLote(Enum):
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    PAUSADO = "PAUSADO"
    COMPLETADO = "COMPLETADO"
