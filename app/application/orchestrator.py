from __future__ import annotations
from app.domain.entities import Paciente, EstadoValidacion, EntidadSeguro
from app.domain.ports import IPacienteRepository, IScraperService

class OrchestratorService:
    def __init__(
        self, 
        repository: IPacienteRepository, 
        scraper: IScraperService
    ) -> None:
        self._repository = repository
        self._scraper = scraper

    def procesar_cola(self) -> None:
        pacientes_pendientes = self._repository.obtener_pendientes()
        for paciente in pacientes_pendientes:
            self._procesar_paciente_individual(paciente)

    def _procesar_paciente_individual(self, paciente: Paciente) -> None:
        try:
            entidad_str, tipo_seguro, registro_cobertura, pdf_p1 = self._scraper.procesar_portal_1(
                paciente.cedula, paciente.fecha_atencion
            )
            
            entidad_limpia = entidad_str.strip().lower()
            registro_limpio = registro_cobertura.strip().lower()
            tipo_seguro_limpio = tipo_seguro.strip()

            if "no registra cobertura" in registro_limpio or tipo_seguro_limpio.lower() == "no registra cobertura":
                paciente.estado = EstadoValidacion.INVALIDO
                paciente.entidad_detectada = EntidadSeguro.NINGUNA
                paciente.aporta = "NINGUNA"
                paciente.es_auditoria_rojo = True
                self._repository.actualizar_estado(paciente)
                return

            paciente.estado = EstadoValidacion.VALIDO
            paciente.pdf_p1_propio_bytes = pdf_p1
            paciente.aporta = tipo_seguro_limpio

            if "issfa" in entidad_limpia:
                paciente.entidad_detectada = EntidadSeguro.ISSFA
                self._ejecutar_ruta_portal_3_directo(paciente)
            elif "isspol" in entidad_limpia:
                paciente.entidad_detectada = EntidadSeguro.ISSPOL
                self._ejecutar_ruta_portal_3_directo(paciente)
            elif "iess" in entidad_limpia:
                paciente.entidad_detectada = EntidadSeguro.IESS
                
                cedula_prov = self._scraper.extraer_acreditador_portal_2(paciente)
                if cedula_prov:
                    paciente.seguro_derivado = True
                    paciente.cedula_acreditador = cedula_prov
                    
                    _, _, _, pdf_acreditador = self._scraper.procesar_portal_1(cedula_prov, paciente.fecha_atencion)
                    paciente.pdf_p1_acreditador_bytes = pdf_acreditador
                
                self._ejecutar_ruta_completa_p2_p3(paciente)
            else:
                paciente.estado = EstadoValidacion.INVALIDO
                paciente.entidad_detectada = EntidadSeguro.NINGUNA
                paciente.aporta = "NINGUNA"
                paciente.es_auditoria_rojo = True

            self._repository.actualizar_estado(paciente)

        except Exception:
            paciente.estado = EstadoValidacion.PENDIENTE
            self._repository.actualizar_estado(paciente)

    def _ejecutar_ruta_portal_3_directo(self, paciente: Paciente) -> None:
        pass

    def _ejecutar_ruta_completa_p2_p3(self, paciente: Paciente) -> None:
        pass
