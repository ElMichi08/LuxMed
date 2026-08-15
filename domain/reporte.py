from __future__ import annotations

from domain.estados import EstadoPaciente

# Mapeo confirmado por el propietario (2026-08-15) — docs/BDD/12_exportacion_excel_resultado.feature.
# "Error Portal 2" agrupa ERROR_PORTAL_2 y PDF_CORRUPTO_PORTAL_2 (ambos fallos técnicos sin
# resolver) a propósito; SIN_COBERTURA_PORTAL_2 comparte texto con NO_ENCONTRADO porque los dos
# son el mismo tipo de señal de negocio ("el departamento de origen no actualizó su fuente").
# PENDIENTE no tiene entrada: el Excel solo se genera cuando el lote ya terminó, sin pacientes
# en ese estado.
_ESTADO_A_TEXTO_EXCEL: dict[EstadoPaciente, str] = {
    EstadoPaciente.COMPLETADO: "Correcto",
    EstadoPaciente.NO_ENCONTRADO: "Desactualizado",
    EstadoPaciente.SIN_COBERTURA_PORTAL_2: "Desactualizado",
    EstadoPaciente.CEDULA_INVALIDA: "CI no válida",
    EstadoPaciente.ERROR_PORTAL_1: "Error Portal 1",
    EstadoPaciente.ERROR_PORTAL_2: "Error Portal 2",
    EstadoPaciente.PDF_CORRUPTO_PORTAL_2: "Error Portal 2",
}


def estado_a_texto_excel(estado: EstadoPaciente) -> str:
    return _ESTADO_A_TEXTO_EXCEL[estado]
