from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QSize, Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QFont, QResizeEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.application.dto import DetallePaciente, PasoRuta
from app.infrastructure.ui.theme.icons import icono
from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, TIPOGRAFIA
from app.infrastructure.ui.widgets.status_chip import StatusChip

ANCHO = 420
ALTO_CABECERA = 74
ALTO_PIE = 68
NOTA_REPROCESO = "Solo disponible cuando el estado es ERROR_PORTAL_N"
NOTA_SIN_PASOS = "Este paciente no llegó a consultarse en ningún portal."
NOTA_SIN_EXPEDIENTE = "Sin expediente consolidado todavía."


def _paso_fallido(paso: PasoRuta) -> bool:
    return paso.nota is not None and paso.nota.startswith("sin")


class _EtiquetaElidida(QLabel):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._texto_completo = ""

    def establecer_texto(self, texto: str) -> None:
        self._texto_completo = texto
        self.setToolTip(texto)
        self._actualizar_elision()

    def minimumSizeHint(self) -> QSize:
        return QSize(20, self.fontMetrics().height())

    def resizeEvent(self, event: QResizeEvent | None) -> None:
        super().resizeEvent(event)
        self._actualizar_elision()

    def _actualizar_elision(self) -> None:
        metrica = self.fontMetrics()
        elidido = metrica.elidedText(
            self._texto_completo, Qt.TextElideMode.ElideRight, self.width()
        )
        super().setText(elidido)


class PatientDetailPanel(QFrame):
    cerrado = pyqtSignal()
    reproceso_solicitado = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("panel_detalle")
        self.setFixedWidth(ANCHO)
        self._paciente_id: str | None = None
        self._expediente_ruta: Path | None = None

        cabecera = self._crear_cabecera()

        self._area = QScrollArea()
        self._area.setWidgetResizable(True)
        self._area.setFrameShape(QFrame.Shape.NoFrame)
        self._contenido = QWidget()
        self._disposicion_contenido = QVBoxLayout(self._contenido)
        self._disposicion_contenido.setContentsMargins(0, 0, 0, 0)
        self._disposicion_contenido.setSpacing(0)
        self._disposicion_contenido.addStretch(1)
        self._area.setWidget(self._contenido)

        pie = self._crear_pie()

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(0)
        disposicion.addWidget(cabecera)
        disposicion.addWidget(self._area, 1)
        disposicion.addWidget(pie)

    def _crear_cabecera(self) -> QFrame:
        cabecera = QFrame()
        cabecera.setObjectName("cabecera_detalle")
        cabecera.setFixedHeight(ALTO_CABECERA)

        self._nombre = _EtiquetaElidida()
        self._nombre.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_titulo,
                TIPOGRAFIA.peso_semibold,
            )
        )

        self._chip_estado = StatusChip()

        boton_cerrar = QPushButton()
        boton_cerrar.setObjectName("boton_cerrar_detalle")
        boton_cerrar.setIcon(icono("close", COLORES.tinta_sec, 14))
        boton_cerrar.setFixedSize(26, 26)
        boton_cerrar.clicked.connect(self.cerrado.emit)

        fila_1 = QHBoxLayout()
        fila_1.setSpacing(ESPACIADO.sm)
        fila_1.addWidget(self._nombre, 1)
        fila_1.addWidget(self._chip_estado)
        fila_1.addWidget(boton_cerrar)

        etiqueta_cedula = QLabel("Cédula:")
        etiqueta_cedula.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base))
        etiqueta_cedula.setStyleSheet(f"color: {COLORES.tinta_ter};")

        self._valor_cedula = QLabel("")
        self._valor_cedula.setFont(
            QFont(
                TIPOGRAFIA.familia_mono,
                TIPOGRAFIA.tamano_subtitulo,
                TIPOGRAFIA.peso_semibold,
            )
        )

        boton_copiar = QPushButton()
        boton_copiar.setObjectName("boton_copiar")
        boton_copiar.setIcon(icono("content_copy", COLORES.tinta_sec, 14))
        boton_copiar.setFixedSize(24, 24)
        boton_copiar.setToolTip("Copiar cédula")
        boton_copiar.clicked.connect(self._copiar_cedula)

        fila_2 = QHBoxLayout()
        fila_2.setSpacing(ESPACIADO.sm)
        fila_2.addWidget(etiqueta_cedula)
        fila_2.addWidget(self._valor_cedula)
        fila_2.addWidget(boton_copiar)
        fila_2.addStretch(1)

        disposicion = QVBoxLayout(cabecera)
        disposicion.setContentsMargins(
            ESPACIADO.md, ESPACIADO.sm, ESPACIADO.md, ESPACIADO.sm
        )
        disposicion.setSpacing(ESPACIADO.xs)
        disposicion.addLayout(fila_1)
        disposicion.addLayout(fila_2)
        return cabecera

    def _crear_pie(self) -> QFrame:
        pie = QFrame()
        pie.setObjectName("pie_detalle")
        pie.setFixedHeight(ALTO_PIE)

        self._boton_reprocesar = QPushButton("Reprocesar paciente")
        self._boton_reprocesar.setIcon(icono("refresh", COLORES.tinta_ter, 15))
        self._boton_reprocesar.setEnabled(False)
        self._boton_reprocesar.clicked.connect(self._al_reprocesar)

        nota = QLabel(NOTA_REPROCESO)
        nota.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_etiqueta))
        nota.setStyleSheet(f"color: {COLORES.tinta_ter};")
        nota.setAlignment(Qt.AlignmentFlag.AlignCenter)

        disposicion = QVBoxLayout(pie)
        disposicion.setContentsMargins(
            ESPACIADO.md, ESPACIADO.sm, ESPACIADO.md, ESPACIADO.sm
        )
        disposicion.setSpacing(ESPACIADO.xxs)
        disposicion.addWidget(self._boton_reprocesar)
        disposicion.addWidget(nota)
        return pie

    def mostrar_detalle(self, detalle: DetallePaciente) -> None:
        self._paciente_id = detalle.fila.paciente_id
        self._nombre.establecer_texto(detalle.fila.nombre)
        self._chip_estado.establecer_estado(detalle.fila.estado)
        self._valor_cedula.setText(detalle.fila.cedula)

        self._limpiar_contenido()
        self._disposicion_contenido.insertWidget(0, self._crear_bloque_datos(detalle))
        self._disposicion_contenido.insertWidget(1, self._crear_bloque_ruta(detalle))
        self._disposicion_contenido.insertWidget(
            2, self._crear_bloque_expediente(detalle)
        )

        self._boton_reprocesar.setEnabled(detalle.reprocesable)

    def limpiar(self) -> None:
        self._paciente_id = None
        self._expediente_ruta = None
        self._nombre.establecer_texto("")
        self._valor_cedula.setText("")
        self._limpiar_contenido()
        self._boton_reprocesar.setEnabled(False)

    def _limpiar_contenido(self) -> None:
        while self._disposicion_contenido.count() > 1:
            item = self._disposicion_contenido.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()

    def _crear_campo(
        self, etiqueta: str, valor: str, color: str | None = None
    ) -> QWidget:
        contenedor = QWidget()
        disposicion = QVBoxLayout(contenedor)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(2)
        etiqueta_label = QLabel(etiqueta.upper())
        etiqueta_label.setFont(
            QFont(
                TIPOGRAFIA.familia_narrow,
                TIPOGRAFIA.tamano_etiqueta,
                TIPOGRAFIA.peso_semibold,
            )
        )
        etiqueta_label.setStyleSheet(f"color: {COLORES.tinta_ter};")
        valor_label = QLabel(valor)
        valor_label.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_subtitulo,
                TIPOGRAFIA.peso_medio,
            )
        )
        valor_label.setStyleSheet(f"color: {color or COLORES.tinta};")
        disposicion.addWidget(etiqueta_label)
        disposicion.addWidget(valor_label)
        return contenedor

    def _crear_bloque_datos(self, detalle: DetallePaciente) -> QFrame:
        bloque = QFrame()
        bloque.setObjectName("bloque_detalle")
        rejilla = QGridLayout(bloque)
        rejilla.setContentsMargins(
            ESPACIADO.md, ESPACIADO.md, ESPACIADO.md, ESPACIADO.md
        )
        rejilla.setHorizontalSpacing(ESPACIADO.lg)
        rejilla.setVerticalSpacing(ESPACIADO.md)
        rejilla.setColumnStretch(0, 1)
        rejilla.setColumnStretch(1, 1)

        texto_rama = (
            f"Rama {detalle.fila.rama.value}" if detalle.fila.rama is not None else "—"
        )
        if detalle.fila.seguro_derivado is None:
            texto_derivado, color_derivado = "—", None
        elif detalle.fila.seguro_derivado:
            texto_derivado, color_derivado = "Sí", COLORES.verde
        else:
            texto_derivado, color_derivado = "No", COLORES.tinta_sec

        rejilla.addWidget(self._crear_campo("Rama", texto_rama), 0, 0)
        rejilla.addWidget(
            self._crear_campo("Seguro derivado", texto_derivado, color_derivado), 0, 1
        )
        rejilla.addWidget(
            self._crear_campo("Cédula del titular", detalle.cedula_titular or "—"), 1, 0
        )
        rejilla.addWidget(
            self._crear_campo("Cobertura", detalle.cobertura or "—"), 1, 1
        )
        return bloque

    def _crear_bloque_ruta(self, detalle: DetallePaciente) -> QFrame:
        bloque = QFrame()
        bloque.setObjectName("bloque_detalle")
        disposicion = QVBoxLayout(bloque)
        disposicion.setContentsMargins(
            ESPACIADO.md, ESPACIADO.md, ESPACIADO.md, ESPACIADO.md
        )
        disposicion.setSpacing(ESPACIADO.sm)

        cabecera_bloque = QHBoxLayout()
        titulo = QLabel("Ruta ejecutada")
        titulo.setFont(
            QFont(
                TIPOGRAFIA.familia_narrow,
                TIPOGRAFIA.tamano_etiqueta,
                TIPOGRAFIA.peso_semibold,
            )
        )
        titulo.setStyleSheet(f"color: {COLORES.tinta_sec};")
        cabecera_bloque.addWidget(titulo)
        cabecera_bloque.addStretch(1)

        if detalle.pasos:
            resueltos = sum(1 for paso in detalle.pasos if not _paso_fallido(paso))
            contador = QLabel(f"{resueltos}/{len(detalle.pasos)} pasos resueltos")
            contador.setFont(QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_etiqueta))
            contador.setStyleSheet(f"color: {COLORES.tinta_ter};")
            cabecera_bloque.addWidget(contador)
        disposicion.addLayout(cabecera_bloque)

        if not detalle.pasos:
            vacio = QLabel(NOTA_SIN_PASOS)
            vacio.setWordWrap(True)
            vacio.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base))
            vacio.setStyleSheet(f"color: {COLORES.tinta_sec};")
            disposicion.addWidget(vacio)
        else:
            for paso in detalle.pasos:
                disposicion.addWidget(self._crear_paso(paso))

        return bloque

    def _crear_paso(self, paso: PasoRuta) -> QWidget:
        fallido = _paso_fallido(paso)
        contenedor = QWidget()
        disposicion = QHBoxLayout(contenedor)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(ESPACIADO.sm)

        color_circulo = COLORES.rojo if fallido else COLORES.verde
        circulo = QLabel()
        circulo.setFixedSize(16, 16)
        circulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        circulo.setStyleSheet(f"background-color: {color_circulo}; border-radius: 8px;")
        circulo.setPixmap(
            icono("close" if fallido else "check", COLORES.blanco, 10).pixmap(10, 10)
        )

        columna = QVBoxLayout()
        columna.setSpacing(1)
        titulo_paso = QLabel(paso.etiqueta)
        titulo_paso.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_subtitulo,
                TIPOGRAFIA.peso_medio,
            )
        )
        columna.addWidget(titulo_paso)

        partes = [paso.hora.strftime("%H:%M:%S")]
        if paso.tamano_kb is not None:
            partes.append(f"{paso.tamano_kb} KB")
        if paso.nota is not None:
            partes.append(paso.nota)
        subtitulo = QLabel(" · ".join(partes))
        subtitulo.setFont(QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_etiqueta))
        subtitulo.setStyleSheet(
            f"color: {COLORES.rojo if fallido else COLORES.tinta_sec};"
        )
        columna.addWidget(subtitulo)

        disposicion.addWidget(circulo, 0, Qt.AlignmentFlag.AlignTop)
        disposicion.addLayout(columna, 1)
        return contenedor

    def _crear_bloque_expediente(self, detalle: DetallePaciente) -> QFrame:
        bloque = QFrame()
        bloque.setObjectName("bloque_detalle")
        disposicion = QVBoxLayout(bloque)
        disposicion.setContentsMargins(
            ESPACIADO.md, ESPACIADO.md, ESPACIADO.md, ESPACIADO.md
        )
        disposicion.setSpacing(ESPACIADO.sm)

        titulo = QLabel("Expediente")
        titulo.setFont(
            QFont(
                TIPOGRAFIA.familia_narrow,
                TIPOGRAFIA.tamano_etiqueta,
                TIPOGRAFIA.peso_semibold,
            )
        )
        titulo.setStyleSheet(f"color: {COLORES.tinta_sec};")
        disposicion.addWidget(titulo)

        if detalle.expediente is None:
            self._expediente_ruta = None
            vacio = QLabel(NOTA_SIN_EXPEDIENTE)
            vacio.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base))
            vacio.setStyleSheet(f"color: {COLORES.tinta_sec};")
            disposicion.addWidget(vacio)
            return bloque

        self._expediente_ruta = detalle.expediente.ruta
        tarjeta = QFrame()
        tarjeta.setObjectName("tarjeta_expediente")
        disposicion_tarjeta = QHBoxLayout(tarjeta)
        disposicion_tarjeta.setContentsMargins(
            ESPACIADO.sm, ESPACIADO.sm, ESPACIADO.sm, ESPACIADO.sm
        )
        disposicion_tarjeta.setSpacing(ESPACIADO.sm)

        icono_pdf = QLabel()
        icono_pdf.setPixmap(icono("picture_as_pdf", COLORES.rojo, 24).pixmap(24, 24))

        columna = QVBoxLayout()
        columna.setSpacing(2)
        nombre_archivo = _EtiquetaElidida()
        nombre_archivo.setFont(
            QFont(
                TIPOGRAFIA.familia_mono,
                TIPOGRAFIA.tamano_base,
                TIPOGRAFIA.peso_semibold,
            )
        )
        nombre_archivo.establecer_texto(detalle.expediente.nombre_archivo)
        subtitulo = QLabel(
            f"{detalle.expediente.documentos} documentos combinados · {detalle.expediente.tamano_kb} KB"
        )
        subtitulo.setWordWrap(True)
        subtitulo.setFont(QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_etiqueta))
        subtitulo.setStyleSheet(f"color: {COLORES.tinta_ter};")
        columna.addWidget(nombre_archivo)
        columna.addWidget(subtitulo)

        boton_ver = QPushButton("Ver")
        boton_ver.setProperty("variante", "secundario")
        boton_ver.clicked.connect(self._abrir_expediente)

        boton_carpeta = QPushButton()
        boton_carpeta.setProperty("variante", "secundario")
        boton_carpeta.setIcon(icono("folder_open", COLORES.tinta_sec, 16))
        boton_carpeta.setToolTip("Abrir carpeta")
        boton_carpeta.clicked.connect(self._abrir_carpeta)

        disposicion_tarjeta.addWidget(icono_pdf)
        disposicion_tarjeta.addLayout(columna, 1)
        disposicion_tarjeta.addWidget(boton_ver)
        disposicion_tarjeta.addWidget(boton_carpeta)

        disposicion.addWidget(tarjeta)
        return bloque

    def _copiar_cedula(self) -> None:
        portapapeles = QApplication.clipboard()
        if portapapeles is not None:
            portapapeles.setText(self._valor_cedula.text())

    def _abrir_expediente(self) -> None:
        if self._expediente_ruta is not None:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._expediente_ruta)))

    def _abrir_carpeta(self) -> None:
        if self._expediente_ruta is not None:
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(self._expediente_ruta.parent))
            )

    def _al_reprocesar(self) -> None:
        if self._paciente_id is not None:
            self.reproceso_solicitado.emit(self._paciente_id)
