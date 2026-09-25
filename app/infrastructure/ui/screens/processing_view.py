from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import QWidget

from app.application.lote_service import FilaRevision, RevisionLote
from app.application.progreso import AvancePaciente, PasosRuta
from app.domain.entities import EstadoPaciente, Portal, Rama
from app.infrastructure.ui.log_bridge import LineaLog
from app.infrastructure.ui.models.columnas import CENTRO, Columna, ModeloColumnas
from app.infrastructure.ui.models.delegados import (
    ChipDelegate,
    RutaDelegate,
    texto_tooltip_ruta,
)
from app.infrastructure.ui.models.filtro_proxy import FiltroProxy
from app.infrastructure.ui.presentacion import (
    CON_ERROR,
    GRUPOS_FILTRO,
    INVALIDOS,
    TONO_ESTADO,
    texto_edad,
    texto_estado,
    texto_hora,
    texto_rama,
    texto_seguro_derivado,
)
from app.infrastructure.ui.theme.tokens import COLORES, GEOMETRIA
from app.infrastructure.ui.widgets.base import boton, columna, etiqueta, fila, marco
from app.infrastructure.ui.widgets.collapsible_log import CollapsibleLog
from app.infrastructure.ui.widgets.controles import SearchField, SegmentedFilter
from app.infrastructure.ui.widgets.kpi import DefinicionKpi, KpiStrip
from app.infrastructure.ui.widgets.tabla import crear_tabla

INTERVALO_COALESCENCIA_MS = 150
COLUMNA_RUTA = 5
COLUMNA_ESTADO = 6

FILTROS = (
    ("todos", "Todos"),
    ("en_proceso", "En proceso"),
    ("completados", "Completados"),
    ("invalidos", "Inválidos"),
    ("con_error", "Con error"),
)

NOMBRE_PORTAL = {Portal.P1: "Portal 1", Portal.P2: "Portal 2", Portal.P3: "Portal 3"}


@dataclass(frozen=True, slots=True)
class FilaLote:
    revision: FilaRevision
    avance: AvancePaciente

    @property
    def estado(self) -> EstadoPaciente:
        return self.avance.estado


def _f(valor: object) -> FilaLote:
    assert isinstance(valor, FilaLote)
    return valor


def _color_rama(valor: object) -> str | None:
    rama = _f(valor).avance.rama
    return {Rama.A: COLORES.indigo, Rama.B: COLORES.tinta_sec}.get(rama, COLORES.tinta_ter)


def _color_derivado(valor: object) -> str | None:
    derivado = _f(valor).avance.seguro_derivado
    if derivado is None:
        return COLORES.tinta_ter
    return COLORES.verde if derivado else COLORES.tinta_sec


def _color_cedula(valor: object) -> str | None:
    return COLORES.rojo if _f(valor).estado is EstadoPaciente.CEDULA_INVALIDA else COLORES.tinta_sec


def _en_proceso(valor: object) -> bool:
    return _f(valor).estado is EstadoPaciente.EN_PROCESO


def _color_hora(valor: object) -> str | None:
    return COLORES.indigo if _en_proceso(valor) else COLORES.tinta_sec


def _fondo(valor: object) -> str | None:
    return COLORES.indigo_suave if _en_proceso(valor) else None


COLUMNAS = (
    Columna("Paciente", lambda f: _f(f).revision.nombre, None, negrita=lambda _f: True),
    Columna("Cédula", lambda f: _f(f).revision.cedula, 124, mono=True, color=_color_cedula, negrita=_en_proceso),
    Columna("Edad", lambda f: texto_edad(_f(f).revision.edad), 64, CENTRO),
    Columna("Rama", lambda f: texto_rama(_f(f).avance.rama), 70, CENTRO, color=_color_rama, negrita=lambda f: _f(f).avance.rama is Rama.A),
    Columna("Seguro derivado", lambda f: texto_seguro_derivado(_f(f).avance.seguro_derivado), 130, CENTRO, color=_color_derivado, negrita=lambda f: _f(f).avance.seguro_derivado is True),
    Columna("Ruta (P1 · P2 · P3)", lambda f: texto_tooltip_ruta(_f(f).avance.pasos), 160, CENTRO),
    Columna("Estado", lambda f: texto_estado(_f(f).estado), 160),
    Columna("Hora", lambda f: texto_hora(_f(f).avance.hora), 100, CENTRO, mono=True, color=_color_hora, negrita=_en_proceso),
)


def _chip(valor: object) -> tuple[str, str]:
    estado = _f(valor).estado
    return texto_estado(estado), TONO_ESTADO[estado]


def _ruta(valor: object) -> tuple[PasosRuta, bool]:
    fila_lote = _f(valor)
    return fila_lote.avance.pasos, fila_lote.estado is EstadoPaciente.CEDULA_INVALIDA


def _busqueda(valor: object) -> str:
    fila_lote = _f(valor)
    return f"{fila_lote.revision.cedula} {fila_lote.revision.nombre}"


def filas_iniciales(revision: RevisionLote) -> list[FilaLote]:
    hora_carga = datetime.now().time()
    return [
        FilaLote(
            fila_revision,
            AvancePaciente(indice=fila_revision.indice, estado=EstadoPaciente.PENDIENTE)
            if fila_revision.es_valida
            else AvancePaciente(
                indice=fila_revision.indice, estado=EstadoPaciente.CEDULA_INVALIDA, hora=hora_carga
            ),
        )
        for fila_revision in revision.filas
    ]


class ProcessingView(QWidget):
    progreso = pyqtSignal(int, int)
    actividad = pyqtSignal(str, bool)
    primer_avance = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("fondo_blanco")
        self._kpis = KpiStrip(
            (
                DefinicionKpi("total", "Total lote"),
                DefinicionKpi("completados", "Completados", COLORES.verde),
                DefinicionKpi("invalidos", "Inválidos", COLORES.rojo),
                DefinicionKpi("en_proceso", "En proceso", COLORES.indigo),
                DefinicionKpi("pendientes", "Pendientes", COLORES.indigo),
                DefinicionKpi("con_error", "Con error", COLORES.rojo),
            )
        )
        self._busqueda = SearchField(280)
        self._filtro = SegmentedFilter(FILTROS)
        self._nota_entregables = etiqueta("Disponible al cerrar el lote", "nota")
        self.boton_entregables = boton("Generar entregables", nombre_icono="download")
        self.boton_entregables.setEnabled(False)
        barra_layout = fila((12, 0, 12, 0), 12)
        barra_layout.addWidget(self._busqueda)
        barra_layout.addWidget(self._filtro)
        barra_layout.addStretch(1)
        barra_layout.addWidget(self._nota_entregables)
        barra_layout.addWidget(self.boton_entregables)
        barra = marco("barra_filtros", barra_layout)
        barra.setFixedHeight(GEOMETRIA.barra_filtros)

        self._modelo = ModeloColumnas(COLUMNAS, fondo=_fondo, parent=self)
        self._proxy = FiltroProxy(_busqueda, self)
        self._proxy.setSourceModel(self._modelo)
        self._busqueda.textChanged.connect(self._proxy.establecer_texto)
        self._filtro.cambiado.connect(self._aplicar_filtro)
        self._tabla = crear_tabla(
            self._proxy,
            COLUMNAS,
            {COLUMNA_RUTA: RutaDelegate(_ruta), COLUMNA_ESTADO: ChipDelegate(_chip)},
        )
        self.bitacora = CollapsibleLog()

        layout = columna()
        layout.addWidget(self._kpis)
        layout.addWidget(barra)
        layout.addWidget(self._tabla, 1)
        layout.addWidget(self.bitacora)
        self.setLayout(layout)

        self._pendientes: dict[int, AvancePaciente] = {}
        self._recibio_avance = False
        self._temporizador = QTimer(self)
        self._temporizador.setInterval(INTERVALO_COALESCENCIA_MS)
        self._temporizador.timeout.connect(self._volcar)

    def iniciar(self, revision: RevisionLote) -> None:
        self._pendientes.clear()
        self._recibio_avance = False
        self._busqueda.clear()
        self._filtro.seleccionar("todos")
        self.bitacora.limpiar()
        self._modelo.establecer_filas(filas_iniciales(revision))
        self.boton_entregables.setEnabled(False)
        self._nota_entregables.show()
        self._kpis.tile("en_proceso").establecer_activo(True)
        self._refrescar_indicadores()
        self._temporizador.start()

    def aplicar_avance(self, avance: AvancePaciente) -> None:
        self._pendientes[avance.indice] = avance
        if not self._recibio_avance:
            self._recibio_avance = True
            self.primer_avance.emit()

    def finalizar(self) -> None:
        self._temporizador.stop()
        self._volcar()
        self._kpis.tile("en_proceso").establecer_activo(False)
        self._nota_entregables.hide()
        self.actividad.emit("Lote cerrado", False)

    def agregar_log(self, linea: LineaLog) -> None:
        self.bitacora.agregar(linea.texto_plano, linea.resumen)

    def _volcar(self) -> None:
        if not self._pendientes:
            return
        cambios = {
            indice: replace(_f(self._modelo.fila(indice)), avance=avance)
            for indice, avance in self._pendientes.items()
        }
        self._pendientes.clear()
        self._modelo.reemplazar_filas(cambios)
        self._refrescar_indicadores()

    def _refrescar_indicadores(self) -> None:
        estados = [_f(valor).estado for valor in self._modelo.filas]
        conteo = {
            "total": len(estados),
            "completados": estados.count(EstadoPaciente.COMPLETADO),
            "invalidos": sum(1 for estado in estados if estado in INVALIDOS),
            "en_proceso": estados.count(EstadoPaciente.EN_PROCESO),
            "pendientes": estados.count(EstadoPaciente.PENDIENTE),
            "con_error": sum(1 for estado in estados if estado in CON_ERROR),
        }
        self._kpis.establecer_valores(conteo)
        procesados = conteo["total"] - conteo["pendientes"] - conteo["en_proceso"]
        self.progreso.emit(procesados, conteo["total"])
        actual = next(
            (_f(valor).avance.portal_actual for valor in self._modelo.filas if _en_proceso(valor)),
            None,
        )
        if actual is not None:
            self.actividad.emit(f"Consultando: <b>{NOMBRE_PORTAL[actual]}</b>", True)
        elif conteo["pendientes"] or conteo["en_proceso"]:
            self.actividad.emit("Preparando la siguiente consulta…", True)

    def _aplicar_filtro(self, clave: str) -> None:
        estados = GRUPOS_FILTRO[clave]
        self._proxy.establecer_predicado(
            None if estados is None else lambda valor: _f(valor).estado in estados
        )
