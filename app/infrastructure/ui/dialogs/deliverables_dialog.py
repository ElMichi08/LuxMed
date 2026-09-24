from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.application.dto import (
    ResultadoEntregables,
    ResumenLote,
    SeleccionEntregables,
)
from app.infrastructure.ui.theme.icons import icono
from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, TIPOGRAFIA

ANCHO = 560
ALTO_CABECERA = 72


class DeliverablesDialog(QDialog):
    generar_solicitado = pyqtSignal(object)

    def __init__(
        self, resumen: ResumenLote, carpeta_inicial: Path, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._carpeta = carpeta_inicial
        self.setWindowTitle("Generar entregables")
        self.setModal(True)
        self.setFixedWidth(ANCHO)

        cabecera = self._crear_cabecera(resumen)

        self._casilla_limpio, fila_limpio = self._crear_fila_entregable(
            "table_chart",
            "Excel limpio",
            "Copia idéntica al archivo original, sin cambios.",
            f"{resumen.cabecera.total_filas} filas",
        )
        self._casilla_auditado, fila_auditado = self._crear_fila_entregable(
            "description",
            "Excel auditado",
            "Igual al original, con las filas en rojo de los pacientes que no terminaron en Completado.",
            f"{resumen.cabecera.total_filas} filas · {resumen.filas_en_rojo} en rojo",
        )
        self._casilla_expedientes, fila_expedientes = self._crear_fila_entregable(
            "folder_zip",
            "Expedientes consolidados",
            "Un PDF por paciente completado, con nombre NOMBRE_CEDULA.pdf, en la carpeta del mes.",
            f"{resumen.expedientes_consolidados} archivos",
        )
        for casilla in (
            self._casilla_limpio,
            self._casilla_auditado,
            self._casilla_expedientes,
        ):
            casilla.setChecked(True)
            casilla.toggled.connect(self._actualizar_boton_generar)

        bloque_carpeta = self._crear_bloque_carpeta()

        cuerpo = QVBoxLayout()
        cuerpo.setContentsMargins(
            ESPACIADO.lg, ESPACIADO.lg, ESPACIADO.lg, ESPACIADO.lg
        )
        cuerpo.setSpacing(ESPACIADO.sm)
        cuerpo.addWidget(fila_limpio)
        cuerpo.addWidget(fila_auditado)
        cuerpo.addWidget(fila_expedientes)
        cuerpo.addSpacing(ESPACIADO.xs)
        cuerpo.addWidget(bloque_carpeta)

        self._boton_cancelar = QPushButton("Cancelar")
        self._boton_cancelar.setProperty("variante", "secundario")
        self._boton_cancelar.clicked.connect(self.reject)

        self._boton_generar = QPushButton()
        self._boton_generar.setProperty("variante", "primario")
        self._boton_generar.setIcon(icono("file_download", COLORES.blanco, 16))
        self._boton_generar.clicked.connect(self._al_generar)

        pie = QFrame()
        pie.setObjectName("pie_dialogo")
        disposicion_pie = QHBoxLayout(pie)
        disposicion_pie.setContentsMargins(
            ESPACIADO.lg, ESPACIADO.sm, ESPACIADO.lg, ESPACIADO.sm
        )
        disposicion_pie.setSpacing(ESPACIADO.sm)
        disposicion_pie.addStretch(1)
        disposicion_pie.addWidget(self._boton_cancelar)
        disposicion_pie.addWidget(self._boton_generar)

        self._pagina_seleccion = QWidget()
        disposicion_seleccion = QVBoxLayout(self._pagina_seleccion)
        disposicion_seleccion.setContentsMargins(0, 0, 0, 0)
        disposicion_seleccion.setSpacing(0)
        disposicion_seleccion.addLayout(cuerpo)
        disposicion_seleccion.addWidget(pie)

        self._disposicion = QVBoxLayout(self)
        self._disposicion.setContentsMargins(0, 0, 0, 0)
        self._disposicion.setSpacing(0)
        self._disposicion.addWidget(cabecera)
        self._disposicion.addWidget(self._pagina_seleccion)

        self._pagina_estado: QWidget | None = None
        self._actualizar_boton_generar()

    def _crear_cabecera(self, resumen: ResumenLote) -> QFrame:
        cabecera = QFrame()
        cabecera.setObjectName("cabecera_dialogo")
        cabecera.setFixedHeight(ALTO_CABECERA)
        disposicion = QHBoxLayout(cabecera)
        disposicion.setContentsMargins(ESPACIADO.lg, 0, ESPACIADO.lg, 0)

        columna_titulo = QVBoxLayout()
        columna_titulo.setSpacing(2)
        titulo = QLabel("Generar entregables")
        titulo.setFont(
            QFont(
                TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_titulo, TIPOGRAFIA.peso_bold
            )
        )
        if resumen.incompleto:
            texto_subtitulo = (
                f"Lote {resumen.cabecera.lote_id} · {resumen.procesados} de "
                f"{resumen.cabecera.total_filas} · incompleto"
            )
        else:
            texto_subtitulo = f"Lote {resumen.cabecera.lote_id} · {resumen.cabecera.total_filas} pacientes"
        subtitulo = QLabel(texto_subtitulo)
        subtitulo.setFont(QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_base))
        subtitulo.setStyleSheet(f"color: {COLORES.tinta_sec};")
        columna_titulo.addWidget(titulo)
        columna_titulo.addWidget(subtitulo)

        boton_cerrar = QPushButton()
        boton_cerrar.setObjectName("boton_cerrar_detalle")
        boton_cerrar.setIcon(icono("close", COLORES.tinta_sec, 14))
        boton_cerrar.setFixedSize(28, 28)
        boton_cerrar.setToolTip("Cerrar")
        boton_cerrar.clicked.connect(self.reject)

        disposicion.addLayout(columna_titulo)
        disposicion.addStretch(1)
        disposicion.addWidget(boton_cerrar)
        return cabecera

    def _crear_fila_entregable(
        self,
        nombre_icono: str,
        titulo: str,
        descripcion: str,
        contador_texto: str,
    ) -> tuple[QCheckBox, QFrame]:
        ancho_contador = 235
        ancho_texto = (
            ANCHO - ESPACIADO.sm * 2 - 20 - 20 - ESPACIADO.sm * 3 - ancho_contador
        )

        fila = QFrame()
        fila.setObjectName("tarjeta_expediente")
        disposicion = QHBoxLayout(fila)
        disposicion.setContentsMargins(
            ESPACIADO.sm, ESPACIADO.sm, ESPACIADO.sm, ESPACIADO.sm
        )
        disposicion.setSpacing(ESPACIADO.sm)

        casilla = QCheckBox()

        icono_label = QLabel()
        icono_label.setPixmap(icono(nombre_icono, COLORES.tinta_sec, 20).pixmap(20, 20))

        columna_texto = QWidget()
        columna_texto.setFixedWidth(ancho_texto)
        disposicion_texto = QVBoxLayout(columna_texto)
        disposicion_texto.setContentsMargins(0, 0, 0, 0)
        disposicion_texto.setSpacing(2)
        titulo_label = QLabel(titulo)
        titulo_label.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_subtitulo,
                TIPOGRAFIA.peso_semibold,
            )
        )
        descripcion_label = QLabel(descripcion)
        descripcion_label.setWordWrap(True)
        descripcion_label.setFixedWidth(ancho_texto)
        descripcion_label.setFont(
            QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base)
        )
        descripcion_label.setStyleSheet(f"color: {COLORES.tinta_sec}; border: none;")
        disposicion_texto.addWidget(titulo_label)
        disposicion_texto.addWidget(descripcion_label)

        contador_label = QLabel(contador_texto)
        contador_label.setFixedWidth(ancho_contador)
        contador_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop
        )
        contador_label.setFont(
            QFont(
                TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_base, TIPOGRAFIA.peso_medio
            )
        )
        contador_label.setStyleSheet("border: none;")

        disposicion.addWidget(casilla, 0, Qt.AlignmentFlag.AlignTop)
        disposicion.addWidget(icono_label, 0, Qt.AlignmentFlag.AlignTop)
        disposicion.addWidget(columna_texto, 0, Qt.AlignmentFlag.AlignTop)
        disposicion.addWidget(contador_label, 0, Qt.AlignmentFlag.AlignTop)
        return casilla, fila

    def _crear_bloque_carpeta(self) -> QFrame:
        bloque = QFrame()
        bloque.setObjectName("bloque_carpeta")
        disposicion = QVBoxLayout(bloque)
        disposicion.setContentsMargins(
            ESPACIADO.sm, ESPACIADO.sm, ESPACIADO.sm, ESPACIADO.sm
        )
        disposicion.setSpacing(ESPACIADO.xs)

        etiqueta = QLabel("CARPETA DE DESTINO")
        etiqueta.setFont(
            QFont(
                TIPOGRAFIA.familia_narrow,
                TIPOGRAFIA.tamano_etiqueta,
                TIPOGRAFIA.peso_semibold,
            )
        )
        etiqueta.setStyleSheet(f"color: {COLORES.tinta_sec}; border: none;")

        fila = QHBoxLayout()
        self._etiqueta_carpeta = QLabel(str(self._carpeta))
        self._etiqueta_carpeta.setFont(
            QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_base)
        )
        self._etiqueta_carpeta.setStyleSheet("border: none;")

        boton_cambiar = QPushButton("Cambiar")
        boton_cambiar.setProperty("variante", "secundario")
        boton_cambiar.setIcon(icono("folder_open", COLORES.tinta_sec, 15))
        boton_cambiar.clicked.connect(self._al_cambiar_carpeta)

        fila.addWidget(self._etiqueta_carpeta, 1)
        fila.addWidget(boton_cambiar)

        disposicion.addWidget(etiqueta)
        disposicion.addLayout(fila)
        return bloque

    def _al_cambiar_carpeta(self) -> None:
        nueva = QFileDialog.getExistingDirectory(
            self, "Elegir carpeta de destino", str(self._carpeta)
        )
        if nueva:
            self._carpeta = Path(nueva)
            self._etiqueta_carpeta.setText(str(self._carpeta))

    def _actualizar_boton_generar(self) -> None:
        total = sum(
            casilla.isChecked()
            for casilla in (
                self._casilla_limpio,
                self._casilla_auditado,
                self._casilla_expedientes,
            )
        )
        self._boton_generar.setText(
            f"Generar {total} entregables" if total != 1 else "Generar 1 entregable"
        )
        self._boton_generar.setEnabled(total > 0)

    def _al_generar(self) -> None:
        seleccion = SeleccionEntregables(
            excel_limpio=self._casilla_limpio.isChecked(),
            excel_auditado=self._casilla_auditado.isChecked(),
            expedientes=self._casilla_expedientes.isChecked(),
            carpeta_destino=self._carpeta,
        )
        self._establecer_generando()
        self.generar_solicitado.emit(seleccion)

    def _establecer_generando(self) -> None:
        for casilla in (
            self._casilla_limpio,
            self._casilla_auditado,
            self._casilla_expedientes,
        ):
            casilla.setEnabled(False)
        self._boton_cancelar.setEnabled(False)
        self._boton_generar.setEnabled(False)
        self._boton_generar.setText("Generando…")

    def mostrar_resultado(self, resultado: ResultadoEntregables) -> None:
        lineas: list[tuple[str, str]] = []
        if self._casilla_limpio.isChecked():
            lineas.append(
                ("table_chart", f"Excel limpio · {resultado.filas_excel} filas")
            )
        if self._casilla_auditado.isChecked():
            lineas.append(
                (
                    "description",
                    (
                        f"Excel auditado · {resultado.filas_excel} filas · "
                        f"{resultado.filas_en_rojo} en rojo"
                    ),
                )
            )
        if self._casilla_expedientes.isChecked():
            lineas.append(
                (
                    "folder_zip",
                    f"Expedientes consolidados · {resultado.expedientes_generados} archivos",
                )
            )
        self._mostrar_pagina_estado(
            "check",
            COLORES.verde,
            "Entregables generados",
            lineas,
            resultado.carpeta,
        )

    def mostrar_error(self, mensaje: str) -> None:
        self._mostrar_pagina_estado(
            "error_outline",
            COLORES.rojo,
            "No se pudieron generar los entregables",
            [("info", mensaje)],
            None,
        )

    def _mostrar_pagina_estado(
        self,
        nombre_icono: str,
        color_icono: str,
        titulo_texto: str,
        lineas: list[tuple[str, str]],
        carpeta: Path | None,
    ) -> None:
        self._pagina_seleccion.hide()
        if self._pagina_estado is not None:
            self._disposicion.removeWidget(self._pagina_estado)
            self._pagina_estado.deleteLater()

        fila_titulo = QHBoxLayout()
        fila_titulo.setSpacing(ESPACIADO.sm)
        icono_titulo = QLabel()
        icono_titulo.setPixmap(icono(nombre_icono, color_icono, 24).pixmap(24, 24))
        titulo = QLabel(titulo_texto)
        titulo.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_titulo,
                TIPOGRAFIA.peso_semibold,
            )
        )
        titulo.setWordWrap(True)
        fila_titulo.addWidget(icono_titulo)
        fila_titulo.addWidget(titulo, 1)

        cuerpo = QVBoxLayout()
        cuerpo.setContentsMargins(
            ESPACIADO.lg, ESPACIADO.lg, ESPACIADO.lg, ESPACIADO.lg
        )
        cuerpo.setSpacing(ESPACIADO.sm)
        cuerpo.addLayout(fila_titulo)
        for nombre_linea, texto_linea in lineas:
            cuerpo.addWidget(self._crear_linea_estado(nombre_linea, texto_linea))
        if carpeta is not None:
            cuerpo.addWidget(self._crear_bloque_resultado_carpeta(carpeta))

        pie = QFrame()
        pie.setObjectName("pie_dialogo")
        disposicion_pie = QHBoxLayout(pie)
        disposicion_pie.setContentsMargins(
            ESPACIADO.lg, ESPACIADO.sm, ESPACIADO.lg, ESPACIADO.sm
        )
        disposicion_pie.setSpacing(ESPACIADO.sm)
        disposicion_pie.addStretch(1)
        if carpeta is not None:
            self._boton_abrir_carpeta = QPushButton("Abrir carpeta")
            self._boton_abrir_carpeta.setProperty("variante", "secundario")
            self._boton_abrir_carpeta.setIcon(
                icono("folder_open", COLORES.tinta_sec, 15)
            )
            self._boton_abrir_carpeta.clicked.connect(
                lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(carpeta)))
            )
            disposicion_pie.addWidget(self._boton_abrir_carpeta)
        boton_cerrar = QPushButton("Cerrar")
        boton_cerrar.setProperty("variante", "primario")
        boton_cerrar.clicked.connect(self.accept)
        disposicion_pie.addWidget(boton_cerrar)

        self._pagina_estado = QWidget()
        disposicion_estado = QVBoxLayout(self._pagina_estado)
        disposicion_estado.setContentsMargins(0, 0, 0, 0)
        disposicion_estado.setSpacing(0)
        disposicion_estado.addLayout(cuerpo)
        disposicion_estado.addWidget(pie)
        self._disposicion.addWidget(self._pagina_estado)
        self._pagina_estado.show()
        self.adjustSize()

    def _crear_linea_estado(self, nombre_icono: str, texto: str) -> QFrame:
        fila = QFrame()
        fila.setObjectName("tarjeta_expediente")
        disposicion = QHBoxLayout(fila)
        disposicion.setContentsMargins(
            ESPACIADO.sm, ESPACIADO.sm, ESPACIADO.sm, ESPACIADO.sm
        )
        disposicion.setSpacing(ESPACIADO.sm)
        icono_label = QLabel()
        icono_label.setPixmap(icono(nombre_icono, COLORES.tinta_sec, 20).pixmap(20, 20))
        icono_label.setStyleSheet("border: none;")
        texto_label = QLabel(texto)
        texto_label.setWordWrap(True)
        texto_label.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base))
        texto_label.setStyleSheet("border: none;")
        disposicion.addWidget(icono_label)
        disposicion.addWidget(texto_label, 1)
        return fila

    def _crear_bloque_resultado_carpeta(self, carpeta: Path) -> QFrame:
        bloque = QFrame()
        bloque.setObjectName("bloque_carpeta")
        disposicion = QVBoxLayout(bloque)
        disposicion.setContentsMargins(
            ESPACIADO.sm, ESPACIADO.sm, ESPACIADO.sm, ESPACIADO.sm
        )
        disposicion.setSpacing(ESPACIADO.xs)
        etiqueta = QLabel("CARPETA DE DESTINO")
        etiqueta.setFont(
            QFont(
                TIPOGRAFIA.familia_narrow,
                TIPOGRAFIA.tamano_etiqueta,
                TIPOGRAFIA.peso_semibold,
            )
        )
        etiqueta.setStyleSheet(f"color: {COLORES.tinta_sec}; border: none;")
        ruta = QLabel(str(carpeta))
        ruta.setWordWrap(True)
        ruta.setFont(QFont(TIPOGRAFIA.familia_mono, TIPOGRAFIA.tamano_base))
        ruta.setStyleSheet("border: none;")
        disposicion.addWidget(etiqueta)
        disposicion.addWidget(ruta)
        return bloque
