from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.application.dto import FilaError
from app.infrastructure.ui.models.errors_table_model import (
    COLUMNA_ESTADO,
    ErrorsTableModel,
)
from app.infrastructure.ui.models.status_chip_delegate import StatusChipDelegate
from app.infrastructure.ui.theme.icons import icono
from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, GEOMETRIA, TIPOGRAFIA
from app.infrastructure.ui.widgets.empty_state import EmptyState

ANCHOS_COLUMNAS = (40, 210, 120, 230, 220, 120, 190, 150)
ALTO_CABECERA_TABLA = 34
ALTO_PIE = 52


class ErrorsView(QWidget):
    reproceso_solicitado = pyqtSignal(tuple)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._modelo = ErrorsTableModel()
        self._modelo.seleccion_cambiada.connect(self._actualizar_pie)

        titulo = QLabel("Pendientes por error")
        titulo.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_titulo_grande,
                TIPOGRAFIA.peso_semibold,
            )
        )

        self._subtitulo = QLabel("")
        self._subtitulo.setWordWrap(True)
        self._subtitulo.setFont(
            QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_subtitulo)
        )
        self._subtitulo.setStyleSheet(f"color: {COLORES.tinta_sec};")

        cabecera_pagina = QVBoxLayout()
        cabecera_pagina.setContentsMargins(
            ESPACIADO.xxl, ESPACIADO.xl, ESPACIADO.xxl, ESPACIADO.md
        )
        cabecera_pagina.setSpacing(4)
        cabecera_pagina.addWidget(titulo)
        cabecera_pagina.addWidget(self._subtitulo)

        self._estado_vacio = EmptyState(
            "check",
            "No hay errores pendientes",
            "Todos los pacientes se procesaron sin fallas.",
        )
        self._estado_vacio.hide()

        self._tabla = QTableView()
        self._tabla.setModel(self._modelo)
        self._tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tabla.setShowGrid(False)
        self._tabla.setAlternatingRowColors(False)
        self._tabla.setWordWrap(False)
        self._tabla.setTextElideMode(Qt.TextElideMode.ElideRight)
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

        self._contenedor_tabla = QFrame()
        self._contenedor_tabla.setObjectName("tarjeta")
        disposicion_tabla_contenedor = QVBoxLayout(self._contenedor_tabla)
        disposicion_tabla_contenedor.setContentsMargins(0, 0, 0, 0)
        disposicion_tabla_contenedor.addWidget(self._tabla)

        self._etiqueta_seleccion = QLabel("")
        self._etiqueta_seleccion.setFont(
            QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base)
        )

        self._boton_reintentar = QPushButton("Reintentar seleccionados")
        self._boton_reintentar.setProperty("variante", "primario")
        self._boton_reintentar.setIcon(icono("refresh", COLORES.blanco, 16))
        self._boton_reintentar.clicked.connect(self._al_reintentar)

        self._pie = QFrame()
        self._pie.setObjectName("tarjeta")
        self._pie.setFixedHeight(ALTO_PIE)
        disposicion_pie = QHBoxLayout(self._pie)
        disposicion_pie.setContentsMargins(ESPACIADO.lg, 0, ESPACIADO.lg, 0)
        disposicion_pie.addWidget(self._etiqueta_seleccion)
        disposicion_pie.addStretch(1)
        disposicion_pie.addWidget(self._boton_reintentar)

        cuerpo = QVBoxLayout()
        cuerpo.setContentsMargins(ESPACIADO.xxl, 0, ESPACIADO.xxl, ESPACIADO.xl)
        cuerpo.setSpacing(ESPACIADO.md)
        cuerpo.addWidget(self._contenedor_tabla, 1)
        cuerpo.addWidget(self._pie)
        cuerpo.addWidget(self._estado_vacio, 1)

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(0)
        disposicion.addLayout(cabecera_pagina)
        disposicion.addLayout(cuerpo, 1)

        self._actualizar_pie()

    def mostrar_errores(self, errores: tuple[FilaError, ...]) -> None:
        self._modelo.establecer_filas(errores)
        total = len(errores)
        hay_errores = total > 0
        self._contenedor_tabla.setVisible(hay_errores)
        self._pie.setVisible(hay_errores)
        self._estado_vacio.setVisible(not hay_errores)
        self._subtitulo.setVisible(hay_errores)
        self._subtitulo.setText(
            f"{total} pacientes quedaron sin completar su ruta. "
            "Reintentar no vuelve a consultar los portales ya resueltos."
        )
        self._actualizar_pie()

    def _actualizar_pie(self) -> None:
        seleccionados = self._modelo.total_seleccionados()
        total = self._modelo.rowCount()
        self._etiqueta_seleccion.setText(
            f"{seleccionados} de {total} pacientes seleccionados · "
            "Los portales ya capturados no se volverán a consultar"
        )
        self._boton_reintentar.setEnabled(seleccionados > 0)

    def _al_reintentar(self) -> None:
        self.reproceso_solicitado.emit(self._modelo.ids_seleccionados())
