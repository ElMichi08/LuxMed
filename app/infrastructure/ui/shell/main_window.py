from __future__ import annotations

from collections.abc import Callable
from enum import Enum

from PyQt6.QtGui import QCloseEvent
from PyQt6.QtWidgets import QMainWindow, QStackedWidget, QWidget

from app.infrastructure.ui.screens.logs_view import LogsView
from app.infrastructure.ui.screens.processing_view import ProcessingView
from app.infrastructure.ui.screens.review_view import ReviewView
from app.infrastructure.ui.screens.settings_view import SettingsView
from app.infrastructure.ui.screens.summary_view import SummaryView
from app.infrastructure.ui.screens.upload_view import UploadView
from app.infrastructure.ui.widgets.animaciones import cambiar_con_fundido
from app.infrastructure.ui.widgets.base import columna, fila
from app.infrastructure.ui.widgets.loading_overlay import LoadingOverlay
from app.infrastructure.ui.widgets.nav_rail import NavRail
from app.infrastructure.ui.widgets.status_bar import StatusBar
from app.infrastructure.ui.widgets.top_bar import TopBar

TITULO_VENTANA = "LuxMed"
TAMANO_INICIAL = (1280, 800)
TAMANO_MINIMO = (1100, 700)


class PaginaLote(Enum):
    CARGA = 0
    REVISION = 1
    PROCESO = 2
    RESUMEN = 3


class Seccion(str, Enum):
    LOTE = "lote"
    LOGS = "logs"
    HISTORIAL = "historial"
    AJUSTES = "ajustes"


def _pila(paginas: tuple[QWidget, ...]) -> QStackedWidget:
    pila = QStackedWidget()
    pila.setObjectName("paginas")
    for pagina in paginas:
        pila.addWidget(pagina)
    return pila


class MainWindow(QMainWindow):
    def __init__(self, usuario: str, version: str) -> None:
        super().__init__()
        self.setWindowTitle(TITULO_VENTANA)
        self.resize(*TAMANO_INICIAL)
        self.setMinimumSize(*TAMANO_MINIMO)
        self._confirmar_cierre: Callable[[], bool] = lambda: True

        self.top_bar = TopBar(usuario)
        self.rail = NavRail(version)
        self.rail.agregar(Seccion.LOTE, "Lote", "dataset")
        self.rail.agregar(Seccion.LOGS, "Logs", "warning")
        self.rail.agregar(Seccion.HISTORIAL, "Historial", "history", habilitado=False, ayuda="Historial disponible en una próxima versión")
        self.rail.agregar(Seccion.AJUSTES, "Ajustes", "settings")
        self.rail.seleccionado.connect(self.mostrar_seccion)
        self.status_bar = StatusBar()

        self.upload = UploadView()
        self.review = ReviewView()
        self.processing = ProcessingView()
        self.summary = SummaryView()
        self.logs = LogsView()
        self.settings = SettingsView()
        self._pila_lote = _pila((self.upload, self.review, self.processing, self.summary))
        self._secciones = {Seccion.LOTE: self._pila_lote, Seccion.LOGS: self.logs, Seccion.AJUSTES: self.settings}
        self._pila_principal = _pila(tuple(self._secciones.values()))

        self.processing.progreso.connect(self.status_bar.mostrar_progreso)
        self.processing.actividad.connect(self.status_bar.mostrar_actividad)
        self.logs.errores_cambiados.connect(self.rail.item(Seccion.LOGS).establecer_insignia)

        cuerpo = fila()
        cuerpo.addWidget(self.rail)
        cuerpo.addWidget(self._pila_principal, 1)
        layout = columna()
        layout.addWidget(self.top_bar)
        layout.addLayout(cuerpo, 1)
        layout.addWidget(self.status_bar)
        central = QWidget()
        central.setObjectName("lienzo")
        central.setLayout(layout)
        self.setCentralWidget(central)
        self.overlay = LoadingOverlay(central)
        self.ir_a_lote(PaginaLote.CARGA)

    def establecer_confirmacion_cierre(self, confirmar: Callable[[], bool]) -> None:
        self._confirmar_cierre = confirmar

    def mostrar_seccion(self, clave: str) -> None:
        seccion = Seccion(clave)
        self.rail.marcar(seccion)
        cambiar_con_fundido(self._pila_principal, self._secciones[seccion])
        self._refrescar_barra_estado()

    def ir_a_lote(self, pagina: PaginaLote) -> None:
        destino = self._pila_lote.widget(pagina.value)
        if destino is not None:
            cambiar_con_fundido(self._pila_lote, destino)
        self.mostrar_seccion(Seccion.LOTE)

    @property
    def pagina_lote(self) -> PaginaLote:
        return PaginaLote(self._pila_lote.currentIndex())

    def _refrescar_barra_estado(self) -> None:
        en_proceso = (
            self._pila_principal.currentWidget() is self._pila_lote
            and self.pagina_lote is PaginaLote.PROCESO
        )
        self.status_bar.setVisible(en_proceso)

    def closeEvent(self, event: QCloseEvent | None) -> None:
        if event is None:
            return
        if self._confirmar_cierre():
            event.accept()
        else:
            event.ignore()
