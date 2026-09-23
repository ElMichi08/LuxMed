from __future__ import annotations
import re
from app.domain.entities import Paciente, EstadoValidacion

class ValidatorService:
    def __init__(self) -> None:
        self._patron_cedula = re.compile(r"^\d{10}$")

    def higienizar_y_clasificar(self, paciente: Paciente) -> None:
        cedula_limpia = str(paciente.cedula).strip()
        
        if not self._patron_cedula.match(cedula_limpia):
            paciente.estado = EstadoValidacion.INVALIDO
            paciente.es_auditoria_rojo = True
            return

        paciente.cedula = cedula_limpia
        paciente.estado = EstadoValidacion.PENDIENTE