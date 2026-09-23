from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import IntEnum, StrEnum
from pathlib import Path


class EstadoPaciente(StrEnum):
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADO = "COMPLETADO"
    CEDULA_INVALIDA = "CEDULA_INVALIDA"
    NO_ENCONTRADO = "NO_ENCONTRADO"
    ERROR_PORTAL_1 = "ERROR_PORTAL_1"
    ERROR_PORTAL_2 = "ERROR_PORTAL_2"
    ERROR_PORTAL_3 = "ERROR_PORTAL_3"


class Rama(StrEnum):
    A = "A"
    B = "B"


class EstadoLote(StrEnum):
    SIN_INICIAR = "SIN_INICIAR"
    EN_CURSO = "EN_CURSO"
    FINALIZADO = "FINALIZADO"
    DETENIDO = "DETENIDO"


class Portal(IntEnum):
    P1 = 1
    P2 = 2
    P3 = 3


class EstadoPaso(StrEnum):
    PENDIENTE = "PENDIENTE"
    EN_CURSO = "EN_CURSO"
    RESUELTO = "RESUELTO"
    OMITIDO = "OMITIDO"
    FALLIDO = "FALLIDO"


class MotivoDetencion(StrEnum):
    SESION_EXPIRADA = "SESION_EXPIRADA"
    CIERRE_APLICACION = "CIERRE_APLICACION"


class AccionOperador(StrEnum):
    LOGIN_PORTAL_3 = "LOGIN_PORTAL_3"
    CAPTCHA_PORTAL_2 = "CAPTCHA_PORTAL_2"


class DecisionOperador(StrEnum):
    CANCELAR_LOGIN = "CANCELAR_LOGIN"
    REINTENTAR_CAPTCHA = "REINTENTAR_CAPTCHA"
    MARCAR_ERROR_PORTAL_2 = "MARCAR_ERROR_PORTAL_2"


@dataclass(frozen=True, slots=True)
class RutaPortales:
    p1: EstadoPaso
    p2: EstadoPaso
    p3: EstadoPaso


@dataclass(frozen=True, slots=True)
class PacienteRef:
    paciente_id: str
    nombre: str
    cedula: str


@dataclass(frozen=True, slots=True)
class FilaPaciente:
    paciente_id: str
    nombre: str
    cedula: str
    edad: int
    rama: Rama | None
    seguro_derivado: bool | None
    ruta: RutaPortales
    estado: EstadoPaciente
    hora: datetime | None


@dataclass(frozen=True, slots=True)
class ContadoresLote:
    total: int
    completados: int
    invalidos: int
    en_proceso: int
    pendientes: int
    con_error: int


@dataclass(frozen=True, slots=True)
class LineaBitacora:
    hora: datetime
    portal: Portal | None
    mensaje: str


@dataclass(frozen=True, slots=True)
class ProgresoLote:
    procesados: int
    total: int
    portal_actual: Portal | None
    contadores: ContadoresLote


@dataclass(frozen=True, slots=True)
class SolicitudOperador:
    accion: AccionOperador
    paciente: PacienteRef | None


@dataclass(frozen=True, slots=True)
class CabeceraLote:
    lote_id: str
    archivo: str
    total_filas: int
    estado: EstadoLote


@dataclass(frozen=True, slots=True)
class ConteoEstado:
    estado: EstadoPaciente
    total: int
    rama_a: int | None
    rama_b: int | None


@dataclass(frozen=True, slots=True)
class ResumenLote:
    cabecera: CabeceraLote
    procesados: int
    pendientes: int
    conteos: tuple[ConteoEstado, ...]
    hora_inicio: datetime | None
    hora_fin: datetime | None
    duracion: timedelta | None
    filas_en_rojo: int
    expedientes_consolidados: int
    incompleto: bool


@dataclass(frozen=True, slots=True)
class ResultadoEjecucion:
    estado_lote: EstadoLote
    motivo_detencion: MotivoDetencion | None
    resumen: ResumenLote


@dataclass(frozen=True, slots=True)
class FilaRevision:
    fila_excel: int
    nombre: str
    cedula: str
    fecha_nacimiento: date
    edad: int
    seguro: str
    establecimiento: str
    motivo_descarte: str | None


@dataclass(frozen=True, slots=True)
class PreviewLote:
    cabecera: CabeceraLote
    listos: tuple[FilaRevision, ...]
    descartados: tuple[FilaRevision, ...]
    menores_de_edad_listos: int


@dataclass(frozen=True, slots=True)
class PasoRuta:
    portal: Portal
    etiqueta: str
    hora: datetime
    tamano_kb: int | None
    nota: str | None


@dataclass(frozen=True, slots=True)
class ExpedienteConsolidado:
    nombre_archivo: str
    documentos: int
    tamano_kb: int
    ruta: Path


@dataclass(frozen=True, slots=True)
class DetallePaciente:
    fila: FilaPaciente
    cedula_titular: str | None
    cobertura: str | None
    pasos: tuple[PasoRuta, ...]
    expediente: ExpedienteConsolidado | None
    reprocesable: bool


@dataclass(frozen=True, slots=True)
class FilaError:
    paciente_id: str
    nombre: str
    cedula: str
    portal_fallido: Portal
    motivo: str
    intentos: int
    intentos_maximos: int
    ultimo_intento: datetime
    estado: EstadoPaciente


@dataclass(frozen=True, slots=True)
class SesionUsuario:
    usuario: str
    iniciales: str


@dataclass(frozen=True, slots=True)
class SeleccionEntregables:
    excel_limpio: bool
    excel_auditado: bool
    expedientes: bool
    carpeta_destino: Path


@dataclass(frozen=True, slots=True)
class ResultadoEntregables:
    carpeta: Path
    filas_excel: int
    filas_en_rojo: int
    expedientes_generados: int
