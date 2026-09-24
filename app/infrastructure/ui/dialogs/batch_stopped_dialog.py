from __future__ import annotations

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.application.dto import MotivoDetencion, ResultadoEjecucion
from app.infrastructure.ui.theme.icons import icono
from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, TIPOGRAFIA

ANCHO = 480
ALTO_CABECERA = 48
TITULOS_MOTIVO: dict[MotivoDetencion, str] = {
    MotivoDetencion.SESION_EXPIRADA: "La sesión del Portal 3 expiró",
    MotivoDetencion.CIERRE_APLICACION: "El lote se detuvo al cerrar la aplicación",
}
NOTA_ARCHIVOS = (
    "Los archivos de salida generados hasta el momento permanecen intactos en disco."
)


class BatchStoppedDialog(QDialog):
    def __init__(
        self, resultado: ResultadoEjecucion, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        titulo_texto = (
            TITULOS_MOTIVO.get(resultado.motivo_detencion)
            if resultado.motivo_detencion
            else None
        )
        titulo_texto = titulo_texto or "El lote se detuvo"
        self.setWindowTitle(titulo_texto)
        self.setModal(True)
        self.setFixedWidth(ANCHO)

        cabecera = QFrame()
        cabecera.setObjectName("cabecera_dialogo")
        cabecera.setFixedHeight(ALTO_CABECERA)
        disposicion_cabecera = QHBoxLayout(cabecera)
        disposicion_cabecera.setContentsMargins(ESPACIADO.lg, 0, ESPACIADO.lg, 0)
        disposicion_cabecera.setSpacing(ESPACIADO.sm)
        icono_titulo = QLabel()
        icono_titulo.setPixmap(icono("error_outline", COLORES.rojo, 20).pixmap(20, 20))
        titulo = QLabel(titulo_texto)
        titulo.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_subtitulo,
                TIPOGRAFIA.peso_semibold,
            )
        )
        titulo.setWordWrap(True)
        disposicion_cabecera.addWidget(icono_titulo)
        disposicion_cabecera.addWidget(titulo, 1)

        resumen = resultado.resumen
        texto = QLabel(
            f"El lote se detuvo. Los {resumen.procesados} pacientes ya procesados se conservan. "
            f"Para continuar con los {resumen.pendientes} pendientes, inicia un lote nuevo con el listado."
        )
        texto.setWordWrap(True)
        texto.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_subtitulo))

        caja_metricas = QFrame()
        caja_metricas.setObjectName("caja_estado_tecnico")
        disposicion_caja = QVBoxLayout(caja_metricas)
        disposicion_caja.setContentsMargins(
            ESPACIADO.md, ESPACIADO.md, ESPACIADO.md, ESPACIADO.md
        )
        disposicion_caja.setSpacing(ESPACIADO.sm)

        rejilla = QGridLayout()
        rejilla.setColumnStretch(0, 1)
        rejilla.setColumnStretch(1, 1)
        rejilla.addWidget(
            self._crear_metrica(
                "Procesados y conservados", resumen.procesados, COLORES.verde
            ),
            0,
            0,
        )
        rejilla.addWidget(
            self._crear_metrica(
                "Pendientes restantes", resumen.pendientes, COLORES.indigo
            ),
            0,
            1,
        )
        disposicion_caja.addLayout(rejilla)

        separador = QFrame()
        separador.setFixedHeight(1)
        separador.setStyleSheet(f"background-color: {COLORES.filete_suave};")
        disposicion_caja.addWidget(separador)

        fila_nota = QHBoxLayout()
        fila_nota.setSpacing(ESPACIADO.xs)
        icono_nota = QLabel()
        icono_nota.setPixmap(icono("info", COLORES.tinta_sec, 14).pixmap(14, 14))
        nota = QLabel(NOTA_ARCHIVOS)
        nota.setWordWrap(True)
        nota.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_etiqueta))
        nota.setStyleSheet(f"color: {COLORES.tinta_sec};")
        fila_nota.addWidget(icono_nota)
        fila_nota.addWidget(nota, 1)
        disposicion_caja.addLayout(fila_nota)

        cuerpo = QVBoxLayout()
        cuerpo.setContentsMargins(
            ESPACIADO.xl, ESPACIADO.lg, ESPACIADO.xl, ESPACIADO.lg
        )
        cuerpo.setSpacing(ESPACIADO.md)
        cuerpo.addWidget(texto)
        cuerpo.addWidget(caja_metricas)

        boton_entendido = QPushButton("Entendido")
        boton_entendido.setProperty("variante", "primario")
        boton_entendido.clicked.connect(self.accept)

        pie = QFrame()
        pie.setObjectName("pie_dialogo")
        disposicion_pie = QHBoxLayout(pie)
        disposicion_pie.setContentsMargins(
            ESPACIADO.md, ESPACIADO.sm, ESPACIADO.md, ESPACIADO.sm
        )
        disposicion_pie.addStretch(1)
        disposicion_pie.addWidget(boton_entendido)

        disposicion = QVBoxLayout(self)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(0)
        disposicion.addWidget(cabecera)
        disposicion.addLayout(cuerpo)
        disposicion.addWidget(pie)

    def _crear_metrica(self, etiqueta: str, valor: int, color: str) -> QWidget:
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
        etiqueta_label.setStyleSheet(f"color: {COLORES.tinta_sec};")
        etiqueta_label.setWordWrap(True)
        valor_label = QLabel(str(valor))
        valor_label.setFont(
            QFont(
                TIPOGRAFIA.familia_mono,
                TIPOGRAFIA.tamano_titulo,
                TIPOGRAFIA.peso_semibold,
            )
        )
        valor_label.setStyleSheet(f"color: {color};")
        disposicion.addWidget(etiqueta_label)
        disposicion.addWidget(valor_label)
        return contenedor
