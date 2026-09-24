from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.application.dto import ConteoEstado, ResumenLote
from app.infrastructure.ui.theme.icons import icono
from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, TIPOGRAFIA
from app.infrastructure.ui.widgets.status_chip import StatusChip

ANCHO_CONTENIDO = 1140
ANCHO_COLUMNA_ESTADO = 260
ANCHO_COLUMNA_NUMERO = 140
ALTO_FILA = 40
COLUMNAS_NUMERICAS = ("Total", "Rama A", "Rama B")


class SummaryView(QWidget):
    entregables_solicitados = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        titulo = QLabel("Resumen del lote")
        titulo.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_titulo_grande,
                TIPOGRAFIA.peso_bold,
            )
        )

        self._subtitulo = QLabel("")
        self._subtitulo.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base))
        self._subtitulo.setStyleSheet(f"color: {COLORES.tinta_sec};")

        columna_titulo = QVBoxLayout()
        columna_titulo.setSpacing(2)
        columna_titulo.addWidget(titulo)
        columna_titulo.addWidget(self._subtitulo)

        self._boton_entregables = QPushButton("Generar entregables")
        self._boton_entregables.setProperty("variante", "primario")
        self._boton_entregables.setIcon(icono("download", COLORES.blanco, 16))
        self._boton_entregables.clicked.connect(self.entregables_solicitados.emit)

        fila_encabezado = QHBoxLayout()
        fila_encabezado.addLayout(columna_titulo)
        fila_encabezado.addStretch(1)
        fila_encabezado.addWidget(self._boton_entregables, 0, Qt.AlignmentFlag.AlignTop)

        self._panel_tiempos = QFrame()
        self._panel_tiempos.setObjectName("tarjeta")
        self._disposicion_tiempos = QHBoxLayout(self._panel_tiempos)
        self._disposicion_tiempos.setContentsMargins(0, 0, 0, 0)
        self._disposicion_tiempos.setSpacing(0)

        self._tabla_conteos = QFrame()
        self._tabla_conteos.setObjectName("tarjeta")
        self._disposicion_tabla = QVBoxLayout(self._tabla_conteos)
        self._disposicion_tabla.setContentsMargins(0, 0, 0, 0)
        self._disposicion_tabla.setSpacing(0)

        self._notas = QLabel("")
        self._notas.setWordWrap(True)
        self._notas.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base))
        self._notas.setStyleSheet(f"color: {COLORES.tinta_sec};")

        contenido = QWidget()
        contenido.setFixedWidth(ANCHO_CONTENIDO)
        disposicion_contenido = QVBoxLayout(contenido)
        disposicion_contenido.setContentsMargins(0, 0, 0, 0)
        disposicion_contenido.setSpacing(ESPACIADO.lg)
        disposicion_contenido.addLayout(fila_encabezado)
        disposicion_contenido.addWidget(self._panel_tiempos)
        disposicion_contenido.addWidget(self._tabla_conteos)
        disposicion_contenido.addWidget(self._notas)
        disposicion_contenido.addStretch(1)

        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.Shape.NoFrame)
        contenedor_centrado = QWidget()
        disposicion_centrada = QHBoxLayout(contenedor_centrado)
        disposicion_centrada.setContentsMargins(
            ESPACIADO.xxl, ESPACIADO.xl, ESPACIADO.xxl, ESPACIADO.xl
        )
        disposicion_centrada.addStretch(1)
        disposicion_centrada.addWidget(contenido)
        disposicion_centrada.addStretch(1)
        area.setWidget(contenedor_centrado)

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.addWidget(area)

    def mostrar_resumen(self, resumen: ResumenLote) -> None:
        archivo = resumen.cabecera.archivo
        if resumen.incompleto:
            self._subtitulo.setText(
                f"Lote incompleto: se procesaron {resumen.procesados} de "
                f"{resumen.cabecera.total_filas} filas de {archivo}"
            )
        else:
            self._subtitulo.setText(
                f"Procesamiento finalizado con éxito para las {resumen.cabecera.total_filas} filas de {archivo}"
            )

        self._limpiar_layout(self._disposicion_tiempos)
        for indice, (etiqueta, valor) in enumerate(
            (
                ("Hora de inicio", self._formatear_hora(resumen.hora_inicio)),
                ("Hora de fin", self._formatear_hora(resumen.hora_fin)),
                ("Duración", self._formatear_duracion(resumen)),
            )
        ):
            widget = self._crear_metrica_tiempo(
                etiqueta, valor, borde_derecho=indice < 2
            )
            self._disposicion_tiempos.addWidget(widget, 1)

        self._limpiar_layout(self._disposicion_tabla)
        self._disposicion_tabla.addWidget(self._crear_fila_encabezado_tabla())
        for conteo in resumen.conteos:
            self._disposicion_tabla.addWidget(self._crear_fila_conteo(conteo))
        self._disposicion_tabla.addWidget(self._crear_fila_total(resumen))

        nota_total = "El total de cada fila incluye a todos los pacientes de ese estado, aunque no se conozca su rama."
        nota_rojo = f"{resumen.filas_en_rojo} filas quedarán en rojo en el Excel auditado (todo estado distinto de COMPLETADO)."
        self._notas.setText(f"·  {nota_total}\n·  {nota_rojo}")

    def _formatear_hora(self, momento: datetime | None) -> str:
        if momento is None:
            return "—"
        return momento.strftime("%H:%M")

    def _formatear_duracion(self, resumen: ResumenLote) -> str:
        if resumen.duracion is None:
            return "—"
        segundos_totales = int(resumen.duracion.total_seconds())
        horas, resto = divmod(segundos_totales, 3600)
        minutos = resto // 60
        if horas:
            return f"{horas} h {minutos} min"
        return f"{minutos} min"

    def _crear_metrica_tiempo(
        self, etiqueta: str, valor: str, borde_derecho: bool
    ) -> QWidget:
        contenedor = QFrame()
        if borde_derecho:
            contenedor.setStyleSheet(f"border-right: 1px solid {COLORES.filete};")
        disposicion = QVBoxLayout(contenedor)
        disposicion.setContentsMargins(
            ESPACIADO.lg, ESPACIADO.lg, ESPACIADO.lg, ESPACIADO.lg
        )
        disposicion.setSpacing(4)
        etiqueta_label = QLabel(etiqueta.upper())
        etiqueta_label.setFont(
            QFont(
                TIPOGRAFIA.familia_narrow,
                TIPOGRAFIA.tamano_etiqueta,
                TIPOGRAFIA.peso_semibold,
            )
        )
        etiqueta_label.setStyleSheet(f"color: {COLORES.tinta_sec}; border: none;")
        valor_label = QLabel(valor)
        valor_label.setFont(
            QFont(
                TIPOGRAFIA.familia_mono,
                TIPOGRAFIA.tamano_titulo_grande,
                TIPOGRAFIA.peso_bold,
            )
        )
        valor_label.setStyleSheet(f"color: {COLORES.tinta}; border: none;")
        disposicion.addWidget(etiqueta_label)
        disposicion.addWidget(valor_label)
        return contenedor

    def _crear_fila_encabezado_tabla(self) -> QWidget:
        fila = QFrame()
        fila.setObjectName("cabecera_tabla_resumen")
        fila.setFixedHeight(34)
        disposicion = QHBoxLayout(fila)
        disposicion.setContentsMargins(ESPACIADO.md, 0, ESPACIADO.md, 0)
        etiqueta_estado = QLabel("ESTADO")
        etiqueta_estado.setFixedWidth(ANCHO_COLUMNA_ESTADO)
        etiqueta_estado.setFont(
            QFont(
                TIPOGRAFIA.familia_narrow,
                TIPOGRAFIA.tamano_base,
                TIPOGRAFIA.peso_semibold,
            )
        )
        disposicion.addWidget(etiqueta_estado)
        for texto in COLUMNAS_NUMERICAS:
            columna = QLabel(texto.upper())
            columna.setFixedWidth(ANCHO_COLUMNA_NUMERO)
            columna.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            columna.setFont(
                QFont(
                    TIPOGRAFIA.familia_narrow,
                    TIPOGRAFIA.tamano_base,
                    TIPOGRAFIA.peso_semibold,
                )
            )
            disposicion.addWidget(columna)
        disposicion.addStretch(1)
        return fila

    def _crear_fila_conteo(self, conteo: ConteoEstado) -> QWidget:
        fila = QFrame()
        fila.setObjectName("fila_tabla_resumen")
        fila.setFixedHeight(ALTO_FILA)
        disposicion = QHBoxLayout(fila)
        disposicion.setContentsMargins(ESPACIADO.md, 0, ESPACIADO.md, 0)
        contenedor_chip = QWidget()
        contenedor_chip.setFixedWidth(ANCHO_COLUMNA_ESTADO)
        disposicion_chip = QHBoxLayout(contenedor_chip)
        disposicion_chip.setContentsMargins(0, 0, 0, 0)
        disposicion_chip.addWidget(StatusChip(conteo.estado))
        disposicion_chip.addStretch(1)
        disposicion.addWidget(contenedor_chip)
        for valor in (conteo.total, conteo.rama_a, conteo.rama_b):
            disposicion.addWidget(self._etiqueta_numero(valor))
        disposicion.addStretch(1)
        return fila

    def _etiqueta_numero(self, valor: int | None) -> QWidget:
        etiqueta = QLabel(str(valor) if valor is not None else "—")
        etiqueta.setFixedWidth(ANCHO_COLUMNA_NUMERO)
        etiqueta.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        etiqueta.setFont(QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_base))
        etiqueta.setStyleSheet(
            f"color: {COLORES.tinta if valor else COLORES.tinta_ter};"
        )
        return etiqueta

    def _crear_fila_total(self, resumen: ResumenLote) -> QWidget:
        fila = QFrame()
        fila.setObjectName("fila_total_resumen")
        fila.setFixedHeight(42)
        disposicion = QHBoxLayout(fila)
        disposicion.setContentsMargins(ESPACIADO.md, 0, ESPACIADO.md, 0)
        etiqueta = QLabel("Total procesados")
        etiqueta.setFixedWidth(ANCHO_COLUMNA_ESTADO)
        etiqueta.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_base,
                TIPOGRAFIA.peso_semibold,
            )
        )
        disposicion.addWidget(etiqueta)
        total_rama_a = sum(c.rama_a for c in resumen.conteos if c.rama_a is not None)
        total_rama_b = sum(c.rama_b for c in resumen.conteos if c.rama_b is not None)
        for valor in (resumen.procesados, total_rama_a, total_rama_b):
            etiqueta_valor = QLabel(str(valor))
            etiqueta_valor.setFixedWidth(ANCHO_COLUMNA_NUMERO)
            etiqueta_valor.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            etiqueta_valor.setFont(
                QFont(
                    TIPOGRAFIA.familia_mono,
                    TIPOGRAFIA.tamano_base,
                    TIPOGRAFIA.peso_semibold,
                )
            )
            disposicion.addWidget(etiqueta_valor)
        disposicion.addStretch(1)
        return fila

    def _limpiar_layout(self, disposicion: QHBoxLayout | QVBoxLayout) -> None:
        while disposicion.count():
            item = disposicion.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
