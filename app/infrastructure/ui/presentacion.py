from __future__ import annotations

from datetime import date, time, timedelta

from app.domain.entities import EstadoPaciente, Rama

SIN_DATO = "—"

ETIQUETA_ESTADO = {
    EstadoPaciente.PENDIENTE: "Pendiente",
    EstadoPaciente.EN_PROCESO: "En proceso",
}

TONO_ESTADO = {
    EstadoPaciente.PENDIENTE: "neutro",
    EstadoPaciente.EN_PROCESO: "proceso",
    EstadoPaciente.COMPLETADO: "exito",
    EstadoPaciente.CEDULA_INVALIDA: "alerta",
    EstadoPaciente.NO_ENCONTRADO: "alerta",
    EstadoPaciente.ERROR_PORTAL_1: "alerta",
    EstadoPaciente.ERROR_PORTAL_2: "alerta",
    EstadoPaciente.ERROR_PORTAL_3: "alerta",
}

INVALIDOS = frozenset({EstadoPaciente.CEDULA_INVALIDA, EstadoPaciente.NO_ENCONTRADO})
CON_ERROR = frozenset(
    {EstadoPaciente.ERROR_PORTAL_1, EstadoPaciente.ERROR_PORTAL_2, EstadoPaciente.ERROR_PORTAL_3}
)

GRUPOS_FILTRO: dict[str, frozenset[EstadoPaciente] | None] = {
    "todos": None,
    "en_proceso": frozenset({EstadoPaciente.EN_PROCESO}),
    "completados": frozenset({EstadoPaciente.COMPLETADO}),
    "invalidos": INVALIDOS,
    "con_error": CON_ERROR,
}

ESTADOS_RESUMEN = (
    EstadoPaciente.COMPLETADO,
    EstadoPaciente.CEDULA_INVALIDA,
    EstadoPaciente.NO_ENCONTRADO,
    EstadoPaciente.ERROR_PORTAL_1,
    EstadoPaciente.ERROR_PORTAL_2,
    EstadoPaciente.ERROR_PORTAL_3,
)

RAMAS_POSIBLES = {
    EstadoPaciente.COMPLETADO: frozenset({Rama.A, Rama.B}),
    EstadoPaciente.CEDULA_INVALIDA: frozenset({Rama.SIN_RAMA}),
    EstadoPaciente.NO_ENCONTRADO: frozenset({Rama.SIN_RAMA}),
    EstadoPaciente.ERROR_PORTAL_1: frozenset({Rama.A, Rama.B, Rama.SIN_RAMA}),
    EstadoPaciente.ERROR_PORTAL_2: frozenset({Rama.A}),
    EstadoPaciente.ERROR_PORTAL_3: frozenset({Rama.A, Rama.B}),
    EstadoPaciente.PENDIENTE: frozenset({Rama.A, Rama.B, Rama.SIN_RAMA}),
}


def texto_estado(estado: EstadoPaciente) -> str:
    return ETIQUETA_ESTADO.get(estado, estado.value)


def texto_rama(rama: Rama) -> str:
    return SIN_DATO if rama is Rama.SIN_RAMA else rama.value


def texto_seguro_derivado(valor: bool | None) -> str:
    if valor is None:
        return SIN_DATO
    return "Sí" if valor else "No"


def texto_hora(valor: time | None) -> str:
    return valor.strftime("%H:%M:%S") if valor is not None else SIN_DATO


def texto_fecha(valor: date | None) -> str:
    return valor.isoformat() if valor is not None else SIN_DATO


def texto_edad(edad: int | None, sufijo: str = "") -> str:
    return f"{edad}{sufijo}" if edad is not None else SIN_DATO


def texto_duracion(duracion: timedelta) -> str:
    segundos = int(duracion.total_seconds())
    horas, resto = divmod(segundos, 3600)
    minutos = resto // 60
    if horas:
        return f"{horas} h {minutos} min"
    if minutos:
        return f"{minutos} min"
    return f"{segundos} s"


def texto_conteo(estado: EstadoPaciente, rama: Rama, cantidad: int) -> str:
    if cantidad == 0 and rama not in RAMAS_POSIBLES.get(estado, frozenset()):
        return SIN_DATO
    return str(cantidad)
