from __future__ import annotations

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
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.application.dto import PreviewLote
from app.infrastructure.ui.models.review_table_model import ReviewTableModel
from app.infrastructure.ui.theme.icons import icono
from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, GEOMETRIA, TIPOGRAFIA

ANCHOS_COLUMNAS = (125, 265, 125, 150, 70, 205, 210, 170)
ALTO_CABECERA_TABLA = 34
ALTO_PIE = 56


class _Contador(QFrame):
    def __init__(
        self,
        valor: str,
        etiqueta: str,
        color_valor: str,
        nota: str = "",
        color_nota: str = "",
        borde_derecho: bool = False,
    ) -> None:
        super().__init__()
        if borde_derecho:
            self.setStyleSheet(f"border-right: 1px solid {COLORES.filete};")

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(
            ESPACIADO.md, ESPACIADO.sm, ESPACIADO.md, ESPACIADO.sm
        )
        disposicion.setSpacing(2)

        etiqueta_valor = QLabel(valor)
        etiqueta_valor.setFont(
            QFont(
                TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_cifra, TIPOGRAFIA.peso_bold
            )
        )
        etiqueta_valor.setStyleSheet(f"color: {color_valor}; border: none;")
        disposicion.addWidget(etiqueta_valor)

        etiqueta_texto = QLabel(etiqueta)
        etiqueta_texto.setFont(
            QFont(
                TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base, TIPOGRAFIA.peso_medio
            )
        )
        etiqueta_texto.setStyleSheet(f"color: {COLORES.tinta_sec}; border: none;")
        disposicion.addWidget(etiqueta_texto)

        if nota:
            etiqueta_nota = QLabel(nota)
            etiqueta_nota.setFont(
                QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_etiqueta)
            )
            etiqueta_nota.setStyleSheet(f"color: {color_nota}; border: none;")
            disposicion.addWidget(etiqueta_nota)


class ReviewView(QWidget):
    lote_descartado = pyqtSignal()
    campana_iniciada = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._preview: PreviewLote | None = None
        self._modelo = ReviewTableModel()

        titulo = QLabel("Revisión previa del lote")
        titulo.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_titulo_grande,
                TIPOGRAFIA.peso_semibold,
            )
        )

        self._subtitulo = QLabel("")
        self._subtitulo.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base))
        self._subtitulo.setStyleSheet(f"color: {COLORES.tinta_sec};")

        self._fila_contadores = QFrame()
        self._fila_contadores.setObjectName("fila_contadores")
        self._disposicion_contadores = QHBoxLayout(self._fila_contadores)
        self._disposicion_contadores.setContentsMargins(0, 0, 0, 0)
        self._disposicion_contadores.setSpacing(0)

        self._etiqueta_banner = QLabel("")
        self._etiqueta_banner.setFont(
            QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base)
        )
        self._etiqueta_banner.setWordWrap(True)
        icono_banner = QLabel()
        icono_banner.setPixmap(icono("info", COLORES.tinta_sec, 16).pixmap(16, 16))
        self._banner_menores = QFrame()
        self._banner_menores.setObjectName("banner_info")
        disposicion_banner = QHBoxLayout(self._banner_menores)
        disposicion_banner.setContentsMargins(
            ESPACIADO.md, ESPACIADO.sm, ESPACIADO.md, ESPACIADO.sm
        )
        disposicion_banner.setSpacing(ESPACIADO.sm)
        disposicion_banner.addWidget(icono_banner)
        disposicion_banner.addWidget(self._etiqueta_banner, 1)
        self._banner_menores.hide()

        self._boton_listos = QPushButton("Listos")
        self._boton_listos.setCheckable(True)
        self._boton_listos.setProperty("variante", "pestana")
        self._boton_descartados = QPushButton("Descartados")
        self._boton_descartados.setCheckable(True)
        self._boton_descartados.setProperty("variante", "pestana")
        grupo_pestanas = QButtonGroup(self)
        grupo_pestanas.setExclusive(True)
        grupo_pestanas.addButton(self._boton_listos)
        grupo_pestanas.addButton(self._boton_descartados)
        self._boton_listos.setChecked(True)
        self._boton_listos.toggled.connect(self._al_cambiar_pestana)

        self._buscador = QLineEdit()
        self._buscador.setPlaceholderText("Buscar por cédula o nombre")
        self._buscador.setReadOnly(True)
        self._buscador.setFixedWidth(280)
        self._buscador.setFixedHeight(30)
        self._buscador.addAction(
            icono("search", COLORES.tinta_ter, 16),
            QLineEdit.ActionPosition.LeadingPosition,
        )

        contenedor_pestanas = QFrame()
        contenedor_pestanas.setObjectName("borde_inferior")
        fila_pestanas = QHBoxLayout(contenedor_pestanas)
        fila_pestanas.setContentsMargins(0, 0, 0, ESPACIADO.xxs)
        fila_pestanas.setSpacing(ESPACIADO.xxs)
        fila_pestanas.addWidget(self._boton_listos)
        fila_pestanas.addWidget(self._boton_descartados)
        fila_pestanas.addStretch(1)
        fila_pestanas.addWidget(self._buscador)

        self._tabla = QTableView()
        self._tabla.setModel(self._modelo)
        self._tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tabla.setShowGrid(False)
        self._tabla.setAlternatingRowColors(False)
        self._tabla.setWordWrap(False)
        self._tabla.setTextElideMode(Qt.TextElideMode.ElideRight)
        cabecera_vertical = self._tabla.verticalHeader()
        assert cabecera_vertical is not None
        cabecera_vertical.setVisible(False)
        cabecera_vertical.setDefaultSectionSize(GEOMETRIA.fila_alto)
        cabecera = self._tabla.horizontalHeader()
        assert cabecera is not None
        cabecera.setFixedHeight(ALTO_CABECERA_TABLA)
        cabecera.setFont(
            QFont(
                TIPOGRAFIA.familia_narrow,
                TIPOGRAFIA.tamano_etiqueta,
                TIPOGRAFIA.peso_semibold,
            )
        )
        cabecera.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        cabecera.setStretchLastSection(True)
        for indice, ancho in enumerate(ANCHOS_COLUMNAS):
            self._tabla.setColumnWidth(indice, ancho)

        self._pie_resumen = QLabel("")
        self._pie_resumen.setFont(
            QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base)
        )
        self._pie_resumen.setStyleSheet(f"color: {COLORES.tinta_sec};")

        self._boton_descartar = QPushButton("Descartar lote")
        self._boton_descartar.setProperty("variante", "secundario")
        self._boton_descartar.clicked.connect(self.lote_descartado.emit)

        self._boton_iniciar = QPushButton("Iniciar campaña")
        self._boton_iniciar.setProperty("variante", "primario")
        self._boton_iniciar.clicked.connect(self.campana_iniciada.emit)

        pie = QFrame()
        pie.setObjectName("pie_revision")
        pie.setFixedHeight(ALTO_PIE)
        disposicion_pie = QHBoxLayout(pie)
        disposicion_pie.setContentsMargins(ESPACIADO.xxl, 0, ESPACIADO.xxl, 0)
        disposicion_pie.setSpacing(ESPACIADO.md)
        disposicion_pie.addWidget(self._pie_resumen)
        disposicion_pie.addStretch(1)
        disposicion_pie.addWidget(self._boton_descartar)
        disposicion_pie.addWidget(self._boton_iniciar)

        contenido = QVBoxLayout()
        contenido.setContentsMargins(
            ESPACIADO.xxl, ESPACIADO.xl, ESPACIADO.xxl, ESPACIADO.md
        )
        contenido.setSpacing(ESPACIADO.sm)
        contenido.addWidget(titulo)
        contenido.addWidget(self._subtitulo)
        contenido.addSpacing(ESPACIADO.sm)
        contenido.addWidget(self._fila_contadores)
        contenido.addWidget(self._banner_menores)
        contenido.addSpacing(ESPACIADO.sm)
        contenido.addWidget(contenedor_pestanas)
        contenido.addWidget(self._tabla, 1)

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(0)
        disposicion.addLayout(contenido, 1)
        disposicion.addWidget(pie)

    def mostrar_preview(self, preview: PreviewLote) -> None:
        self._preview = preview
        total = len(preview.listos) + len(preview.descartados)
        self._subtitulo.setText(
            f"Se leyeron {total} filas. Revisa los descartados antes de iniciar."
        )

        while self._disposicion_contadores.count():
            item = self._disposicion_contadores.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()

        self._disposicion_contadores.addWidget(
            _Contador(str(total), "Total de filas", COLORES.tinta, borde_derecho=True)
        )
        self._disposicion_contadores.addWidget(
            _Contador(
                str(len(preview.listos)),
                "Listos para consultar",
                COLORES.verde,
                "Cédula de 10 dígitos válida",
                COLORES.verde,
                borde_derecho=True,
            )
        )
        self._disposicion_contadores.addWidget(
            _Contador(
                str(len(preview.descartados)),
                "Descartados",
                COLORES.rojo,
                "Cédula con longitud distinta a 10 dígitos",
                COLORES.rojo,
            )
        )

        if preview.menores_de_edad_listos > 0:
            self._etiqueta_banner.setText(
                f"{preview.menores_de_edad_listos} menores de edad entre los listos. "
                "Se consultan igual; si no tienen cobertura quedan como No encontrado."
            )
            self._banner_menores.show()
        else:
            self._banner_menores.hide()

        self._boton_listos.setText(f"Listos  {len(preview.listos)}")
        self._boton_descartados.setText(f"Descartados  {len(preview.descartados)}")
        self._boton_listos.setChecked(True)
        self._modelo.establecer_filas(preview.listos)

        self._pie_resumen.setText(
            f"Se consultarán {len(preview.listos)} pacientes. "
            f"Los {len(preview.descartados)} descartados quedarán en rojo en el Excel auditado."
        )

    def _al_cambiar_pestana(self, marcado: bool) -> None:
        if self._preview is None:
            return
        if marcado:
            self._modelo.establecer_filas(self._preview.listos)
        else:
            self._modelo.establecer_filas(self._preview.descartados)
