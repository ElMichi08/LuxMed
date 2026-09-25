from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from enum import Enum

class EstadoValidacion(str, Enum):
    PENDIENTE = "PENDIENTE"
    VALIDO = "VALIDO"
    INVALIDO = "INVALIDO"

class EntidadSeguro(str, Enum):
    IESS = "IESS"
    ISSFA = "ISSFA"
    ISSPOL = "ISSPOL"
    NINGUNA = "NINGUNA"

@dataclass
class Paciente:
    nombre_y_apellidos: str
    cedula: str
    fecha_nacimiento: date
    aporta: str
    fecha_atencion: date
    nom_establecimiento: str
    
    estado: EstadoValidacion = EstadoValidacion.PENDIENTE
    entidad_detectada: EntidadSeguro = EntidadSeguro.NINGUNA
    seguro_derivado: bool = False
    
    pdf_p1_propio_bytes: bytes | None = None
    cedula_acreditador: str | None = None
    pdf_p1_acreditador_bytes: bytes | None = None
    pdf_p3_bytes: bytes | None = None
    pdf_consolidado: bytes | None = None
    
    es_auditoria_rojo: bool = False

    @property
    def edad(self) -> int:
        hoy = date.today()
        return hoy.year - self.fecha_nacimiento.year - (
            (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )

    @property
    def es_menor_de_edad(self) -> bool:
        return self.edad < 18


class EstadoPaciente(str, Enum):
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADO = "COMPLETADO"
    CEDULA_INVALIDA = "CEDULA_INVALIDA"
    NO_ENCONTRADO = "NO_ENCONTRADO"
    ERROR_PORTAL_1 = "ERROR_PORTAL_1"
    ERROR_PORTAL_2 = "ERROR_PORTAL_2"
    ERROR_PORTAL_3 = "ERROR_PORTAL_3"


class Rama(str, Enum):
    A = "A"
    B = "B"
    SIN_RAMA = "SIN_RAMA"


class Portal(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class EstadoPaso(str, Enum):
    PENDIENTE = "PENDIENTE"
    EN_CURSO = "EN_CURSO"
    HECHO = "HECHO"
    OMITIDO = "OMITIDO"
    FALLIDO = "FALLIDO"


@dataclass(frozen=True, slots=True)
class CredencialesPortal3:
    usuario: str
    contrasena: str

    @property
    def completas(self) -> bool:
        return bool(self.usuario.strip()) and bool(self.contrasena)
