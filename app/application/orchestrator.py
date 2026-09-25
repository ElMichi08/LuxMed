from __future__ import annotations
import logging
from collections.abc import Sequence
from datetime import datetime
from app.domain.entities import Paciente, EstadoValidacion, EntidadSeguro, Portal
from app.application.progreso import (
    AvancePaciente,
    IObservadorLote,
    ObservadorNulo,
    RastreadorPaciente,
    ResumenLote,
)
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

    def procesar_pacientes(
        self, cola: Sequence[tuple[int, Paciente]], observador: IObservadorLote
    ) -> ResumenLote:
        inicio = datetime.now()
        resultados: list[AvancePaciente] = []
        detenido = False
        for indice, paciente in cola:
            if observador.detencion_solicitada():
                detenido = True
                break
            rastreador = RastreadorPaciente(indice, observador)
            self._procesar_paciente_individual(paciente, rastreador)
            resultados.append(rastreador.resolver(paciente))
        return ResumenLote(
            inicio=inicio, fin=datetime.now(), resultados=tuple(resultados), detenido=detenido
        )

    def generar_excels(self, pacientes: list[Paciente], ruta_origen: str, ruta_limpio: str, ruta_auditoria: str) -> None:
        if self._excel_handler is None:
            return
        
        self._excel_handler.exportar_excel_limpio(ruta_limpio, pacientes)
        self._excel_handler.exportar_excel_auditoria(ruta_origen, ruta_auditoria, pacientes)

    def _procesar_paciente_individual(
        self, paciente: Paciente, rastreador: RastreadorPaciente | None = None
    ) -> None:
        rastreador = rastreador or RastreadorPaciente(0, ObservadorNulo())
        try:
            logger.info("Procesando paciente %s (%s)", paciente.cedula, paciente.nombre_y_apellidos)
            
            rastreador.iniciar(Portal.P1)
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
                rastreador.marcar_no_encontrado()
                self._repository.actualizar_estado(paciente)
                logger.info("Paciente %s — SIN cobertura, marcado INVALIDO", paciente.cedula)
                return

            rastreador.terminar(Portal.P1, exito=True)
            paciente.estado = EstadoValidacion.VALIDO
            paciente.pdf_p1_propio_bytes = pdf_p1
            paciente.aporta = tipo_seguro_limpio

            if "issfa" in entidad_limpia:
                paciente.entidad_detectada = EntidadSeguro.ISSFA
                rastreador.clasificar(paciente)
                rastreador.omitir(Portal.P2)
                logger.info("Paciente %s — ruta ISSFA → Portal 3 directo", paciente.cedula)
                self._ejecutar_ruta_portal_3_directo(paciente, rastreador)
            elif "isspol" in entidad_limpia:
                paciente.entidad_detectada = EntidadSeguro.ISSPOL
                rastreador.clasificar(paciente)
                rastreador.omitir(Portal.P2)
                logger.info("Paciente %s — ruta ISSPOL → Portal 3 directo", paciente.cedula)
                self._ejecutar_ruta_portal_3_directo(paciente, rastreador)
            elif "iess" in entidad_limpia:
                paciente.entidad_detectada = EntidadSeguro.IESS
                rastreador.clasificar(paciente)
                logger.info("Paciente %s — ruta IESS → Portal 2 + Portal 3", paciente.cedula)
                
                rastreador.iniciar(Portal.P2)
                cedula_prov = self._scraper.extraer_acreditador_portal_2(paciente)
                rastreador.terminar(Portal.P2, exito=True)
                if cedula_prov:
                    paciente.seguro_derivado = True
                    paciente.cedula_acreditador = cedula_prov
                    rastreador.clasificar(paciente)
                    logger.info("Acreditador encontrado: %s", cedula_prov)
                    
                    rastreador.iniciar(Portal.P1)
                    _, _, _, pdf_acreditador = self._scraper.procesar_portal_1(
                        cedula_prov, paciente.fecha_atencion
                    )
                    rastreador.terminar(Portal.P1, exito=True)
                    paciente.pdf_p1_acreditador_bytes = pdf_acreditador
                else:
                    logger.info("Paciente %s — sin proveedor (afiliado directo, sin tabla en Portal 2)", paciente.cedula)
                
                self._ejecutar_ruta_completa_p2_p3(paciente, rastreador)
            else:
                logger.warning("Paciente %s — entidad desconocida: '%s'", paciente.cedula, entidad_limpia)
                paciente.estado = EstadoValidacion.INVALIDO
                paciente.entidad_detectada = EntidadSeguro.NINGUNA
                paciente.aporta = "NINGUNA"
                paciente.es_auditoria_rojo = True
                rastreador.marcar_no_encontrado()

            self._repository.actualizar_estado(paciente)

            if paciente.estado == EstadoValidacion.VALIDO and self._pdf_consolidator is not None:
                paciente.pdf_consolidado = self._pdf_consolidator.consolidar(paciente)
                if paciente.pdf_consolidado is not None:
                    ruta = self._pdf_consolidator.guardar(paciente)
                    if ruta:
                        logger.info("Paciente %s — PDF guardado: %s", paciente.cedula, ruta)

        except Exception as e:
            logger.error("Error procesando paciente %s: %s", paciente.cedula, e, exc_info=True)
            rastreador.fallo_en_curso()
            paciente.estado = EstadoValidacion.PENDIENTE
            self._repository.actualizar_estado(paciente)

    def _ejecutar_ruta_portal_3_directo(self, paciente: Paciente, rastreador: RastreadorPaciente) -> None:
        if self._portal3 is None:
            logger.info("Paciente %s — Portal 3 no disponible, saltando", paciente.cedula)
            rastreador.terminar(Portal.P3, exito=False)
            return
        logger.info("Paciente %s — procesando Portal 3...", paciente.cedula)
        rastreador.iniciar(Portal.P3)
        try:
            pdf_p3 = self._portal3.procesar_portal_3(paciente)
            paciente.pdf_p3_bytes = pdf_p3
            rastreador.terminar(Portal.P3, exito=pdf_p3 is not None)
            logger.info("Paciente %s — Portal 3 OK, pdf: %s", paciente.cedula, f"{len(pdf_p3)} bytes" if pdf_p3 else "None")
        except Exception as e:
            rastreador.terminar(Portal.P3, exito=False)
            logger.error("Paciente %s — Portal 3 fallo: %s", paciente.cedula, e)

    def _ejecutar_ruta_completa_p2_p3(self, paciente: Paciente, rastreador: RastreadorPaciente) -> None:
        if self._portal3 is None:
            logger.info("Paciente %s — Portal 3 no disponible, saltando P3", paciente.cedula)
            rastreador.terminar(Portal.P3, exito=False)
            return
        logger.info("Paciente %s — procesando Portal 3 (ruta IESS)...", paciente.cedula)
        rastreador.iniciar(Portal.P3)
        try:
            pdf_p3 = self._portal3.procesar_portal_3(paciente)
            paciente.pdf_p3_bytes = pdf_p3
            rastreador.terminar(Portal.P3, exito=pdf_p3 is not None)
            logger.info("Paciente %s — Portal 3 OK, pdf: %s", paciente.cedula, f"{len(pdf_p3)} bytes" if pdf_p3 else "None")
        except Exception as e:
            rastreador.terminar(Portal.P3, exito=False)
            logger.error("Paciente %s — Portal 3 fallo: %s", paciente.cedula, e)
