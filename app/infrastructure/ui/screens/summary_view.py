from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QScrollArea, QWidget

from app.application.lote_service import Entregables, RevisionLote
from app.application.progreso import ResumenLote
from app.domain.entities import EstadoPaciente
from app.infrastructure.ui.models.columnas import DERECHA, Columna, ModeloColumnas
from app.infrastructure.ui.models.delegados import ChipDelegate
from app.infrastructure.ui.presentacion import (
    CON_ERROR,
    ESTADOS_RESUMEN,
    TONO_ESTADO,
    texto_duracion,
)
from app.infrastructure.ui.theme.tokens import COLORES, GEOMETRIA
from app.infrastructure.ui.widgets.base import boton, columna, etiqueta, fila
from app.infrastructure.ui.widgets.kpi import DefinicionKpi, panel_kpi
from app.infrastructure.ui.widgets.paneles import Panel, ScreenHeader, lista_de_vinetas
from app.infrastructure.ui.widgets.tabla import crear_tabla

ANCHO_MAXIMO = 1140
TEXTO_TOTAL = "Total procesados"


@dataclass(frozen=True, slots=True)
class FilaConteo:
    estado: EstadoPaciente | None
    total: int


def _c(valor: object) -> FilaConteo:
    assert isinstance(valor, FilaConteo)
    return valor


def _es_total(valor: object) -> bool:
    return _c(valor).estado is None


COLUMNAS = (
    Columna("Estado", lambda f: TEXTO_TOTAL if _es_total(f) else "", None, negrita=_es_total),
    Columna("Total", lambda f: str(_c(f).total), 180, DERECHA, mono=True, negrita=lambda _f: True),
)


def _chip(valor: object) -> tuple[str, str] | None:
    conteo = _c(valor)
    if conteo.estado is None:
        return None
    tono = "neutro" if conteo.estado in CON_ERROR and conteo.total == 0 else TONO_ESTADO[conteo.estado]
    return conteo.estado.value, tono


def _fondo(valor: object) -> str | None:
    return COLORES.fila_total if _es_total(valor) else None


def filas_conteo(resumen: ResumenLote) -> list[FilaConteo]:
    estados = list(ESTADOS_RESUMEN)
    if resumen.contar(EstadoPaciente.PENDIENTE):
        estados.append(EstadoPaciente.PENDIENTE)
    filas = [FilaConteo(estado, resumen.contar(estado)) for estado in estados]
    return [*filas, FilaConteo(None, resumen.total)]


class SummaryView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("lienzo")
        self.boton_nuevo = boton("Nuevo lote")
        self.boton_detalle = boton("Ver pacientes")
        self.boton_entregables = boton("Generar entregables", "primario", "download", alto=36)
        self._encabezado = ScreenHeader(
            "Resumen del lote", (self.boton_detalle, self.boton_nuevo, self.boton_entregables)
        )
        self._tiempos = panel_kpi(
            (
                DefinicionKpi("inicio", "Hora de inicio"),
                DefinicionKpi("fin", "Hora de fin"),
                DefinicionKpi("duracion", "Duración"),
            )
        )
        self._modelo = ModeloColumnas(COLUMNAS, fondo=_fondo, parent=self)
        self._tabla = crear_tabla(self._modelo, COLUMNAS, {0: ChipDelegate(_chip)}, con_borde=True)
        self._notas = columna()

        self._entregables = Panel((16, 12, 16, 12), 4)
        self._ruta_entregables = etiqueta("", "mono")
        self._ruta_entregables.setWordWrap(True)
        self.boton_abrir = boton("Abrir carpeta", nombre_icono="folder_open")
        self.boton_abrir.clicked.connect(self._abrir_carpeta)
        cabecera_entregables = fila(espacio=12)
        cabecera_entregables.addWidget(etiqueta("Entregables generados", "titulo_seccion"), 1)
        cabecera_entregables.addWidget(self.boton_abrir)
        self._entregables.contenido.addLayout(cabecera_entregables)
        self._entregables.contenido.addWidget(self._ruta_entregables)
        self._entregables.hide()
        self._carpeta_entregables = ""

        interno = QWidget()
        interno.setObjectName("lienzo")
        interno.setMaximumWidth(ANCHO_MAXIMO)
        contenido = columna((24, 24, 24, 24), 20)
        contenido.addWidget(self._encabezado)
        contenido.addWidget(self._tiempos)
        contenido.addWidget(self._tabla)
        contenido.addLayout(self._notas)
        contenido.addWidget(self._entregables)
        contenido.addStretch(1)
        interno.setLayout(contenido)
        desplazable = QScrollArea()
        desplazable.setWidgetResizable(True)
        desplazable.setFrameShape(QScrollArea.Shape.NoFrame)
        desplazable.setWidget(interno)
        layout = columna()
        layout.addWidget(desplazable)
        self.setLayout(layout)

    def mostrar(self, revision: RevisionLote, resumen: ResumenLote, carpeta_destino: str) -> None:
        procesados = resumen.total - resumen.contar(EstadoPaciente.PENDIENTE)
        estado = (
            f"Lote detenido: {procesados} de {resumen.total} filas de {revision.nombre_archivo} alcanzaron un estado final."
            if resumen.detenido
            else f"Procesamiento finalizado para las {resumen.total} filas de {revision.nombre_archivo}."
        )
        self._encabezado.establecer_subtitulo(f"{estado}\nCarpeta de salida: {carpeta_destino}")
        self._tiempos.establecer_valores(
            {
                "inicio": resumen.inicio.strftime("%H:%M"),
                "fin": resumen.fin.strftime("%H:%M"),
                "duracion": texto_duracion(resumen.duracion),
            }
        )
        filas = filas_conteo(resumen)
        self._modelo.establecer_filas(filas)
        self._tabla.setFixedHeight(GEOMETRIA.cabecera_tabla + GEOMETRIA.fila * len(filas) + 2)
        self._mostrar_notas(resumen.filas_en_rojo)
        self._entregables.hide()

    def mostrar_entregables(self, entregables: Entregables) -> None:
        self._carpeta_entregables = entregables.carpeta
        self._ruta_entregables.setText(
            f"{entregables.excel_limpio}\n{entregables.excel_auditado}\n{entregables.carpeta_pdfs}"
        )
        self._entregables.show()

    def _mostrar_notas(self, filas_en_rojo: int) -> None:
        while self._notas.count():
            elemento = self._notas.takeAt(0)
            widget = elemento.widget() if elemento is not None else None
            if widget is not None:
                widget.deleteLater()
        self._notas.addWidget(
            lista_de_vinetas(
                (
                    (
                        f'<b style="color:{COLORES.rojo}">{filas_en_rojo} filas</b> quedarán en rojo en el '
                        "Excel auditado (todo estado distinto de COMPLETADO)."
                    ),
                )
            )
        )

    def _abrir_carpeta(self) -> None:
        if self._carpeta_entregables:
            QDesktopServices.openUrl(QUrl.fromLocalFile(self._carpeta_entregables))
