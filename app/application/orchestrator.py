from __future__ import annotations
import logging
from app.domain.entities import Paciente, EstadoValidacion, EntidadSeguro
from app.domain.ports import IPacienteRepository, IScraperService, IPdfConsolidator, IExcelHandler

logger = logging.getLogger(__name__)


class OrchestratorService:
    def __init__(
        self, 
        repository: IPacienteRepository, 
        scraper: IScraperService,
        pdf_consolidator: IPdfConsolidator | None = None,
        portal3_adapter: object | None = None,
        excel_handler: IExcelHandler | None = None,
    ) -> None:
        self._repository = repository
        self._scraper = scraper
        self._pdf_consolidator = pdf_consolidator
        self._portal3 = portal3_adapter
        self._excel_handler = excel_handler

    def procesar_cola(self) -> list[Paciente]:
        pacientes_pendientes = self._repository.obtener_pendientes()
        for paciente in pacientes_pendientes:
            self._procesar_paciente_individual(paciente)
        return pacientes_pendientes

    def generar_excels(self, pacientes: list[Paciente], ruta_origen: str, ruta_limpio: str, ruta_auditoria: str) -> None:
        if self._excel_handler is None:
            return
        
        self._excel_handler.exportar_excel_limpio(ruta_limpio, pacientes)
        self._excel_handler.exportar_excel_auditoria(ruta_origen, ruta_auditoria, pacientes)

    def _procesar_paciente_individual(self, paciente: Paciente) -> None:
        try:
            logger.info("Procesando paciente %s (%s)", paciente.cedula, paciente.nombre_y_apellidos)
            
            entidad_str, tipo_seguro, registro_cobertura, pdf_p1 = self._scraper.procesar_portal_1(
                paciente.cedula, paciente.fecha_atencion
            )
            
            entidad_limpia = entidad_str.strip().lower()
            registro_limpio = registro_cobertura.strip().lower()
            tipo_seguro_limpio = tipo_seguro.strip()

            logger.info(
                "Portal 1 OK — entidad: '%s', tipo_seguro: '%s', registro: '%s'",
                entidad_limpia, tipo_seguro_limpio, registro_limpio,
            )

            if "no registra cobertura" in registro_limpio or tipo_seguro_limpio.lower() == "no registra cobertura":
                paciente.estado = EstadoValidacion.INVALIDO
                paciente.entidad_detectada = EntidadSeguro.NINGUNA
                paciente.aporta = "NINGUNA"
                paciente.es_auditoria_rojo = True
                self._repository.actualizar_estado(paciente)
                logger.info("Paciente %s — SIN cobertura, marcado INVALIDO", paciente.cedula)
                return

            paciente.estado = EstadoValidacion.VALIDO
            paciente.pdf_p1_propio_bytes = pdf_p1
            paciente.aporta = tipo_seguro_limpio

            if "issfa" in entidad_limpia:
                paciente.entidad_detectada = EntidadSeguro.ISSFA
                logger.info("Paciente %s — ruta ISSFA → Portal 3 directo", paciente.cedula)
                self._ejecutar_ruta_portal_3_directo(paciente)
            elif "isspol" in entidad_limpia:
                paciente.entidad_detectada = EntidadSeguro.ISSPOL
                logger.info("Paciente %s — ruta ISSPOL → Portal 3 directo", paciente.cedula)
                self._ejecutar_ruta_portal_3_directo(paciente)
            elif "iess" in entidad_limpia:
                paciente.entidad_detectada = EntidadSeguro.IESS
                logger.info("Paciente %s — ruta IESS → Portal 2 + Portal 3", paciente.cedula)
                
                cedula_prov = self._scraper.extraer_acreditador_portal_2(paciente)
                if cedula_prov:
                    paciente.seguro_derivado = True
                    paciente.cedula_acreditador = cedula_prov
                    logger.info("Acreditador encontrado: %s", cedula_prov)
                    
                    _, _, _, pdf_acreditador = self._scraper.procesar_portal_1(
                        cedula_prov, paciente.fecha_atencion
                    )
                    paciente.pdf_p1_acreditador_bytes = pdf_acreditador
                else:
                    logger.info("Paciente %s — sin proveedor (afiliado directo, sin tabla en Portal 2)", paciente.cedula)
                
                self._ejecutar_ruta_completa_p2_p3(paciente)
            else:
                logger.warning("Paciente %s — entidad desconocida: '%s'", paciente.cedula, entidad_limpia)
                paciente.estado = EstadoValidacion.INVALIDO
                paciente.entidad_detectada = EntidadSeguro.NINGUNA
                paciente.aporta = "NINGUNA"
                paciente.es_auditoria_rojo = True

            self._repository.actualizar_estado(paciente)

            if paciente.estado == EstadoValidacion.VALIDO and self._pdf_consolidator is not None:
                paciente.pdf_consolidado = self._pdf_consolidator.consolidar(paciente)
                if paciente.pdf_consolidado is not None:
                    ruta = self._pdf_consolidator.guardar(paciente)
                    if ruta:
                        logger.info("Paciente %s — PDF guardado: %s", paciente.cedula, ruta)

        except Exception as e:
            logger.error("Error procesando paciente %s: %s", paciente.cedula, e, exc_info=True)
            paciente.estado = EstadoValidacion.PENDIENTE
            self._repository.actualizar_estado(paciente)

    def _ejecutar_ruta_portal_3_directo(self, paciente: Paciente) -> None:
        if self._portal3 is None:
            logger.info("Paciente %s — Portal 3 no disponible, saltando", paciente.cedula)
            return
        logger.info("Paciente %s — procesando Portal 3...", paciente.cedula)
        try:
            pdf_p3 = self._portal3.procesar_portal_3(paciente)
            paciente.pdf_p3_bytes = pdf_p3
            logger.info("Paciente %s — Portal 3 OK, pdf: %s", paciente.cedula, f"{len(pdf_p3)} bytes" if pdf_p3 else "None")
        except Exception as e:
            logger.error("Paciente %s — Portal 3 fallo: %s", paciente.cedula, e)

    def _ejecutar_ruta_completa_p2_p3(self, paciente: Paciente) -> None:
        if self._portal3 is None:
            logger.info("Paciente %s — Portal 3 no disponible, saltando P3", paciente.cedula)
            return
        logger.info("Paciente %s — procesando Portal 3 (ruta IESS)...", paciente.cedula)
        try:
            pdf_p3 = self._portal3.procesar_portal_3(paciente)
            paciente.pdf_p3_bytes = pdf_p3
            logger.info("Paciente %s — Portal 3 OK, pdf: %s", paciente.cedula, f"{len(pdf_p3)} bytes" if pdf_p3 else "None")
        except Exception as e:
            logger.error("Paciente %s — Portal 3 fallo: %s", paciente.cedula, e)
