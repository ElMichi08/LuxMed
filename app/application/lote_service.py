from __future__ import annotations

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

from app.application.orchestrator import OrchestratorService
from app.application.progreso import AvancePaciente, IObservadorLote, ResumenLote
from app.application.validator import ValidatorService
from app.domain.entities import (
    CredencialesPortal3,
    EstadoPaciente,
    EstadoValidacion,
    Paciente,
)
from app.domain.ports import (
    IConfiguracionRepository,
    IExcelHandler,
    IPacienteRepository,
)

logger = logging.getLogger(__name__)

FECHA_NO_LEGIBLE = date(1900, 1, 1)
PRIMERA_FILA_DE_DATOS = 2
PREFIJO_CARPETA_LOTE = "Lote_"

FabricaOrquestador = Callable[[CredencialesPortal3, str], OrchestratorService]


class ErrorLote(Exception):
    pass


class ErrorCargaListado(ErrorLote):
    pass


class ErrorPrecondicion(ErrorLote):
    pass


@dataclass(frozen=True, slots=True)
class FilaRevision:
    indice: int
    fila_excel: int
    nombre: str
    cedula: str
    fecha_nacimiento: date | None
    edad: int | None
    seguro: str
    establecimiento: str
    motivo_descarte: str | None

    @property
    def es_valida(self) -> bool:
        return self.motivo_descarte is None

    @property
    def es_menor(self) -> bool:
        return self.edad is not None and self.edad < 18


@dataclass(frozen=True, slots=True)
class RevisionLote:
    lote_id: str
    ruta_origen: str
    filas: tuple[FilaRevision, ...]
    pacientes: tuple[Paciente, ...] = field(repr=False, compare=False)

    @property
    def nombre_archivo(self) -> str:
        return Path(self.ruta_origen).name

    @property
    def listos(self) -> tuple[FilaRevision, ...]:
        return tuple(fila for fila in self.filas if fila.es_valida)

    @property
    def descartados(self) -> tuple[FilaRevision, ...]:
        return tuple(fila for fila in self.filas if not fila.es_valida)

    @property
    def menores_listos(self) -> int:
        return sum(1 for fila in self.listos if fila.es_menor)


@dataclass(frozen=True, slots=True)
class Entregables:
    carpeta: str
    excel_limpio: str
    excel_auditado: str
    carpeta_pdfs: str


def motivo_descarte(cedula: str) -> str:
    limpia = cedula.strip()
    if not limpia or limpia.lower() == "nan":
        return "Cédula vacía"
    if not limpia.isdigit():
        return "Cédula con caracteres no numéricos"
    return f"Cédula con {len(limpia)} dígitos"


class ServicioLote:
    def __init__(
        self,
        excel: IExcelHandler,
        repositorio: IPacienteRepository,
        validador: ValidatorService,
        configuracion: IConfiguracionRepository,
        fabrica_orquestador: FabricaOrquestador,
    ) -> None:
        self._excel = excel
        self._repositorio = repositorio
        self._validador = validador
        self._configuracion = configuracion
        self._fabrica_orquestador = fabrica_orquestador

    def cargar_listado(self, ruta: str) -> RevisionLote:
        try:
            pacientes = self._excel.leer_pacientes(ruta)
        except Exception as error:
            raise ErrorCargaListado(
                "No se pudo leer el archivo. Verifica que sea un .xlsx con la hoja BASE."
            ) from error
        if not pacientes:
            raise ErrorCargaListado("El archivo no tiene filas de pacientes.")
        filas = tuple(self._revisar(indice, paciente) for indice, paciente in enumerate(pacientes))
        lote_id = self._nuevo_lote_id()
        logger.info("Listado cargado: %s (%d filas) · Lote %s", Path(ruta).name, len(filas), lote_id)
        return RevisionLote(lote_id=lote_id, ruta_origen=ruta, filas=filas, pacientes=tuple(pacientes))

    def verificar_precondiciones(self) -> None:
        if not self._configuracion.obtener_credenciales_portal3().completas:
            raise ErrorPrecondicion(
                "Faltan el usuario o la contraseña del Portal 3. Complétalos en Ajustes."
            )
        if not self._carpeta_salida().is_dir():
            raise ErrorPrecondicion("La carpeta de salida no existe. Elige una en Ajustes.")

    def ejecutar(self, revision: RevisionLote, observador: IObservadorLote) -> ResumenLote:
        self.verificar_precondiciones()
        self._repositorio.guardar_lote(list(revision.pacientes))
        carpeta_pdfs = self._carpeta_lote(revision) / "pdfs"
        orquestador = self._fabrica_orquestador(
            self._configuracion.obtener_credenciales_portal3(), str(carpeta_pdfs)
        )
        cola = [
            (fila.indice, revision.pacientes[fila.indice]) for fila in revision.filas if fila.es_valida
        ]
        logger.info("Campaña iniciada · Lote %s · %d pacientes en cola", revision.lote_id, len(cola))
        resumen = orquestador.procesar_pacientes(cola, observador)
        return self._resumen_completo(revision, resumen)

    def generar_entregables(self, revision: RevisionLote) -> Entregables:
        carpeta = self._carpeta_lote(revision)
        carpeta.mkdir(parents=True, exist_ok=True)
        base = Path(revision.nombre_archivo).stem
        excel_limpio = carpeta / f"{base}_limpio.xlsx"
        excel_auditado = carpeta / f"{base}_auditado.xlsx"
        pacientes = list(revision.pacientes)
        self._excel.exportar_excel_limpio(str(excel_limpio), pacientes)
        self._excel.exportar_excel_auditoria(revision.ruta_origen, str(excel_auditado), pacientes)
        logger.info("Entregables generados en %s", carpeta)
        return Entregables(
            carpeta=str(carpeta),
            excel_limpio=str(excel_limpio),
            excel_auditado=str(excel_auditado),
            carpeta_pdfs=str(carpeta / "pdfs"),
        )

    def _revisar(self, indice: int, paciente: Paciente) -> FilaRevision:
        cedula_original = paciente.cedula
        self._validador.higienizar_y_clasificar(paciente)
        fecha_legible = paciente.fecha_nacimiento != FECHA_NO_LEGIBLE
        valida = paciente.estado is not EstadoValidacion.INVALIDO
        return FilaRevision(
            indice=indice,
            fila_excel=indice + PRIMERA_FILA_DE_DATOS,
            nombre=paciente.nombre_y_apellidos,
            cedula=paciente.cedula,
            fecha_nacimiento=paciente.fecha_nacimiento if fecha_legible else None,
            edad=paciente.edad if fecha_legible else None,
            seguro=paciente.aporta,
            establecimiento=paciente.nom_establecimiento,
            motivo_descarte=None if valida else motivo_descarte(cedula_original),
        )

    def _resumen_completo(self, revision: RevisionLote, resumen: ResumenLote) -> ResumenLote:
        procesados = {avance.indice: avance for avance in resumen.resultados}
        resultados: list[AvancePaciente] = []
        for fila in revision.filas:
            if not fila.es_valida:
                resultados.append(AvancePaciente(indice=fila.indice, estado=EstadoPaciente.CEDULA_INVALIDA))
            elif fila.indice in procesados:
                resultados.append(procesados[fila.indice])
            else:
                revision.pacientes[fila.indice].es_auditoria_rojo = True
                resultados.append(AvancePaciente(indice=fila.indice, estado=EstadoPaciente.PENDIENTE))
        return ResumenLote(
            inicio=resumen.inicio,
            fin=resumen.fin,
            resultados=tuple(resultados),
            detenido=resumen.detenido,
        )

    def _carpeta_salida(self) -> Path:
        return Path(self._configuracion.obtener_carpeta_salida())

    def _carpeta_lote(self, revision: RevisionLote) -> Path:
        return self._carpeta_salida() / f"{PREFIJO_CARPETA_LOTE}{revision.lote_id}"

    def _nuevo_lote_id(self) -> str:
        prefijo = datetime.now().strftime("%Y-%m-%d")
        patron = re.compile(rf"^{PREFIJO_CARPETA_LOTE}{prefijo}-(\d+)$")
        carpeta = self._carpeta_salida()
        existentes = [
            int(coincidencia.group(1))
            for hijo in (carpeta.iterdir() if carpeta.is_dir() else ())
            if (coincidencia := patron.match(hijo.name))
        ]
        return f"{prefijo}-{max(existentes, default=0) + 1:02d}"
