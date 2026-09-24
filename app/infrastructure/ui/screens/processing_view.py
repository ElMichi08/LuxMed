from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.application.dto import (
    CabeceraLote,
    EstadoLote,
    FilaPaciente,
    LineaBitacora,
    ProgresoLote,
    ResultadoEjecucion,
    SolicitudOperador,
)
from app.infrastructure.ui.dialogs.batch_stopped_dialog import BatchStoppedDialog
from app.infrastructure.ui.dialogs.captcha_dialog import CaptchaDialog
from app.infrastructure.ui.dialogs.portal3_login_dialog import Portal3LoginDialog
from app.infrastructure.ui.models.batch_filter_proxy import (
    BatchFilterProxy,
    FiltroEstado,
)
from app.infrastructure.ui.models.batch_table_model import (
    COLUMNA_ESTADO,
    COLUMNA_RUTA,
    BatchTableModel,
)
from app.infrastructure.ui.models.route_dots_delegate import RouteDotsDelegate
from app.infrastructure.ui.models.status_chip_delegate import StatusChipDelegate
from app.infrastructure.ui.screens.patient_detail_panel import PatientDetailPanel
from app.infrastructure.ui.shell.log_panel import LogPanel
from app.infrastructure.ui.shell.status_bar import StatusBar
from app.infrastructure.ui.theme.icons import icono
from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, GEOMETRIA, TIPOGRAFIA
from app.infrastructure.ui.widgets.kpi_tile import KpiTile

ANCHOS_COLUMNAS = (240, 130, 75, 75, 205, 140, 150, 90)
ALTO_CABECERA_TABLA = 34
ALTO_BARRA_FILTROS = 46

FILTROS = (
    (FiltroEstado.TODOS, "Todos"),
    (FiltroEstado.EN_PROCESO, "En proceso"),
    (FiltroEstado.COMPLETADOS, "Completados"),
    (FiltroEstado.INVALIDOS, "Inválidos"),
    (FiltroEstado.CON_ERROR, "Con error"),
)


class ProcessingView(QWidget):
    entregables_solicitados = pyqtSignal()
    paciente_seleccionado = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cabecera: CabeceraLote | None = None
        self._dialogo_login: Portal3LoginDialog | None = None
        self._dialogo_captcha: CaptchaDialog | None = None
        self._dialogo_detenido: BatchStoppedDialog | None = None

        self._modelo = BatchTableModel()
        self._proxy = BatchFilterProxy(self)
        self._proxy.setSourceModel(self._modelo)

        self._kpi_total = KpiTile("Total lote")
        self._kpi_completados = KpiTile("Completados")
        self._kpi_invalidos = KpiTile("Inválidos")
        self._kpi_en_proceso = KpiTile("En proceso")
        self._kpi_pendientes = KpiTile("Pendientes")
        self._kpi_con_error = KpiTile("Con error")
        self._kpi_completados.establecer_color_valor(COLORES.verde)
        self._kpi_invalidos.establecer_color_valor(COLORES.rojo)
        self._kpi_en_proceso.establecer_color_valor(COLORES.indigo)
        self._kpi_pendientes.establecer_color_valor(COLORES.indigo)
        self._kpi_con_error.establecer_color_valor(COLORES.rojo)

        tira_kpi = QFrame()
        tira_kpi.setObjectName("tira_kpi")
        disposicion_kpi = QHBoxLayout(tira_kpi)
        disposicion_kpi.setContentsMargins(0, 0, 0, 0)
        disposicion_kpi.setSpacing(0)
        tiles_kpi = (
            self._kpi_total,
            self._kpi_completados,
            self._kpi_invalidos,
            self._kpi_en_proceso,
            self._kpi_pendientes,
            self._kpi_con_error,
        )
        for indice, tile in enumerate(tiles_kpi):
            if indice < len(tiles_kpi) - 1:
                tile.setStyleSheet(f"border-right: 1px solid {COLORES.filete_suave};")
            disposicion_kpi.addWidget(tile, 1)

        self._buscador = QLineEdit()
        self._buscador.setPlaceholderText("Buscar por cédula o nombre")
        self._buscador.setFixedWidth(270)
        self._buscador.setFixedHeight(30)
        self._buscador.addAction(
            icono("search", COLORES.tinta_ter, 16),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self._buscador.textChanged.connect(self._proxy.establecer_busqueda)

        self._grupo_segmentos = QButtonGroup(self)
        self._grupo_segmentos.setExclusive(True)
        segmentos = QFrame()
        segmentos.setObjectName("segmentos")
        disposicion_segmentos = QHBoxLayout(segmentos)
        disposicion_segmentos.setContentsMargins(0, 0, 0, 0)
        disposicion_segmentos.setSpacing(0)
        self._botones_filtro: dict[FiltroEstado, QPushButton] = {}
        for indice, (filtro, etiqueta) in enumerate(FILTROS):
            boton = QPushButton(etiqueta)
            boton.setCheckable(True)
            variante = "segmento_final" if indice == len(FILTROS) - 1 else "segmento"
            boton.setProperty("variante", variante)
            boton.setFont(
                QFont(
                    TIPOGRAFIA.familia_sans,
                    TIPOGRAFIA.tamano_base,
                    TIPOGRAFIA.peso_medio,
                )
            )
            boton.toggled.connect(self._crear_manejador_filtro(filtro))
            self._grupo_segmentos.addButton(boton)
            self._botones_filtro[filtro] = boton
            disposicion_segmentos.addWidget(boton)
        self._botones_filtro[FiltroEstado.TODOS].setChecked(True)

        self._nota_entregables = QLabel("Disponible al cerrar el lote")
        self._nota_entregables.setFont(
            QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_etiqueta)
        )
        self._nota_entregables.setStyleSheet(f"color: {COLORES.tinta_ter};")

        self._boton_entregables = QPushButton("Generar entregables")
        self._boton_entregables.setIcon(icono("file_download", COLORES.tinta_ter, 16))
        self._boton_entregables.setEnabled(False)
        self._boton_entregables.clicked.connect(self.entregables_solicitados.emit)

        barra_filtros = QFrame()
        barra_filtros.setObjectName("barra_filtros")
        barra_filtros.setFixedHeight(ALTO_BARRA_FILTROS)
        disposicion_filtros = QHBoxLayout(barra_filtros)
        disposicion_filtros.setContentsMargins(ESPACIADO.md, 0, ESPACIADO.md, 0)
        disposicion_filtros.setSpacing(ESPACIADO.md)
        disposicion_filtros.addWidget(self._buscador)
        disposicion_filtros.addWidget(segmentos)
        disposicion_filtros.addStretch(1)
        disposicion_filtros.addWidget(self._nota_entregables)
        disposicion_filtros.addWidget(self._boton_entregables)

        self._tabla = QTableView()
        self._tabla.setModel(self._proxy)
        self._tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tabla.setShowGrid(False)
        self._tabla.setAlternatingRowColors(False)
        self._tabla.setWordWrap(False)
        self._tabla.setTextElideMode(Qt.TextElideMode.ElideRight)
        self._tabla.setItemDelegateForColumn(
            COLUMNA_RUTA, RouteDotsDelegate(self._tabla)
        )
        self._tabla.setItemDelegateForColumn(
            COLUMNA_ESTADO, StatusChipDelegate(self._tabla)
        )
        cabecera_vertical = self._tabla.verticalHeader()
        assert cabecera_vertical is not None
        cabecera_vertical.setVisible(False)
        cabecera_vertical.setDefaultSectionSize(GEOMETRIA.fila_alto)
        cabecera_horizontal = self._tabla.horizontalHeader()
        assert cabecera_horizontal is not None
        cabecera_horizontal.setFixedHeight(ALTO_CABECERA_TABLA)
        cabecera_horizontal.setFont(
            QFont(
                TIPOGRAFIA.familia_narrow,
                TIPOGRAFIA.tamano_etiqueta,
                TIPOGRAFIA.peso_semibold,
            )
        )
        cabecera_horizontal.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        cabecera_horizontal.setStretchLastSection(True)
        for indice, ancho in enumerate(ANCHOS_COLUMNAS):
            self._tabla.setColumnWidth(indice, ancho)

        modelo_seleccion = self._tabla.selectionModel()
        assert modelo_seleccion is not None
        modelo_seleccion.selectionChanged.connect(self._al_cambiar_seleccion)

        self._bitacora = LogPanel()
        self._barra_estado = StatusBar()

        self.panel_detalle = PatientDetailPanel()
        self.panel_detalle.cerrado.connect(self._tabla.clearSelection)
        self.panel_detalle.hide()

        contenido_izquierdo = QWidget()
        contenido = QVBoxLayout(contenido_izquierdo)
        contenido.setContentsMargins(0, 0, 0, 0)
        contenido.setSpacing(0)
        contenido.addWidget(tira_kpi)
        contenido.addWidget(barra_filtros)
        contenido.addWidget(self._tabla, 1)
        contenido.addWidget(self._bitacora)

        self._divisor = QSplitter(Qt.Orientation.Horizontal)
        self._divisor.setChildrenCollapsible(False)
        self._divisor.setHandleWidth(0)
        self._divisor.addWidget(contenido_izquierdo)
        self._divisor.addWidget(self.panel_detalle)
        self._divisor.setStretchFactor(0, 1)
        self._divisor.setStretchFactor(1, 0)

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(0)
        disposicion.addWidget(self._divisor, 1)
        disposicion.addWidget(self._barra_estado)

    def establecer_cabecera(self, cabecera: CabeceraLote) -> None:
        self._cabecera = cabecera
        habilitado = cabecera.estado in (EstadoLote.DETENIDO, EstadoLote.FINALIZADO)
        self._boton_entregables.setEnabled(habilitado)
        self._nota_entregables.setVisible(not habilitado)

    def establecer_filas(self, filas: tuple[FilaPaciente, ...]) -> None:
        self._modelo.reset_rows(filas)

    def aplicar_actualizaciones(self, filas: tuple[FilaPaciente, ...]) -> None:
        self._modelo.apply_updates(filas)

    def agregar_linea_bitacora(self, linea: LineaBitacora) -> None:
        hora = linea.hora.strftime("%H:%M:%S")
        if linea.portal is None:
            self._bitacora.agregar_linea(f"{hora} {linea.mensaje}")
            return
        self._bitacora.agregar_linea(
            f"{hora} Portal {int(linea.portal)} · {linea.mensaje}"
        )

    def actualizar_progreso(self, progreso: ProgresoLote) -> None:
        contadores = progreso.contadores
        self._kpi_total.establecer_valor(contadores.total)
        self._kpi_completados.establecer_valor(contadores.completados)
        self._kpi_invalidos.establecer_valor(contadores.invalidos)
        self._kpi_en_proceso.establecer_valor(contadores.en_proceso)
        self._kpi_pendientes.establecer_valor(contadores.pendientes)
        self._kpi_con_error.establecer_valor(contadores.con_error)
        self._kpi_en_proceso.establecer_activo(contadores.en_proceso > 0)
        self._barra_estado.establecer_progreso(progreso.procesados, progreso.total)
        if progreso.portal_actual is not None:
            self._barra_estado.establecer_actividad(
                f"Consultando: Portal {int(progreso.portal_actual)}"
            )
        else:
            self._barra_estado.establecer_actividad("")

    def mostrar_solicitud_login_portal3(self, es_reproceso: bool = False) -> None:
        self._dialogo_login = Portal3LoginDialog(es_reproceso=es_reproceso, parent=self)
        self._dialogo_login.show()

    def ocultar_solicitud_login_portal3(self) -> None:
        if self._dialogo_login is not None:
            self._dialogo_login.close()
            self._dialogo_login = None

    def mostrar_solicitud_captcha(self, solicitud: SolicitudOperador) -> None:
        self._dialogo_captcha = CaptchaDialog(solicitud, self)
        self._dialogo_captcha.show()

    def ocultar_solicitud_captcha(self) -> None:
        if self._dialogo_captcha is not None:
            self._dialogo_captcha.close()
            self._dialogo_captcha = None

    def mostrar_lote_detenido(self, resultado: ResultadoEjecucion) -> None:
        self._dialogo_detenido = BatchStoppedDialog(resultado, self)
        self._dialogo_detenido.show()

    def ocultar_lote_detenido(self) -> None:
        if self._dialogo_detenido is not None:
            self._dialogo_detenido.close()
            self._dialogo_detenido = None

    def _al_cambiar_seleccion(self) -> None:
        indices = self._tabla.selectionModel()
        if indices is None or not indices.hasSelection():
            self.panel_detalle.limpiar()
            self.panel_detalle.hide()
            return
        indice_proxy = indices.selectedRows()[0]
        indice_fuente = self._proxy.mapToSource(indice_proxy)
        fila = self._modelo.fila_en(indice_fuente.row())
        self.panel_detalle.show()
        self.paciente_seleccionado.emit(fila.paciente_id)

    def _crear_manejador_filtro(self, filtro: FiltroEstado) -> Callable[[bool], None]:
        def _manejador(marcado: bool) -> None:
            if marcado:
                self._proxy.establecer_filtro_estado(filtro)

        return _manejador
