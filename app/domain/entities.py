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
    pdf_p1_bytes: bytes | None = None
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