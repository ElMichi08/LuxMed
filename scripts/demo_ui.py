from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.application.dto import (
    AccionOperador,
    EstadoLote,
    PacienteRef,
    SesionUsuario,
    SolicitudOperador,
)
from app.infrastructure.ui.bootstrap import preparar
from app.infrastructure.ui.dialogs.batch_stopped_dialog import BatchStoppedDialog
from app.infrastructure.ui.dialogs.captcha_dialog import CaptchaDialog
from app.infrastructure.ui.dialogs.close_confirmation_dialog import (
    CloseConfirmationDialog,
)
from app.infrastructure.ui.dialogs.deliverables_dialog import DeliverablesDialog
from app.infrastructure.ui.dialogs.portal3_login_dialog import Portal3LoginDialog
from app.infrastructure.ui.presenters.errors_presenter import ErrorsPresenter
from app.infrastructure.ui.presenters.login_presenter import LoginPresenter
from app.infrastructure.ui.presenters.patient_detail_presenter import (
    PatientDetailPresenter,
)
from app.infrastructure.ui.presenters.review_presenter import ReviewPresenter
from app.infrastructure.ui.presenters.settings_presenter import SettingsPresenter
from app.infrastructure.ui.presenters.summary_presenter import SummaryPresenter
from app.infrastructure.ui.presenters.upload_presenter import UploadPresenter
from app.infrastructure.ui.screens.errors_view import ErrorsView
from app.infrastructure.ui.screens.login_view import LoginView
from app.infrastructure.ui.screens.processing_view import ProcessingView
from app.infrastructure.ui.screens.review_view import ReviewView
from app.infrastructure.ui.screens.settings_view import SettingsView
from app.infrastructure.ui.screens.summary_view import SummaryView
from app.infrastructure.ui.screens.upload_view import UploadView
from app.infrastructure.ui.shell.navigation import Destino, Navigation
from app.infrastructure.ui.shell.rail import Rail
from app.infrastructure.ui.shell.top_bar import TopBar
from app.infrastructure.ui.theme.tokens import COLORES, ESPACIADO, TIPOGRAFIA
from tests.ui.fakes.dataset import (
    cabecera_simulada,
    filas_paciente_simuladas,
    preview_lote_simulado,
    progreso_simulado,
    resultado_detenido_simulado,
    resumen_lote_simulado,
)
from tests.ui.fakes.ports import (
    FakeBatchIntake,
    FakeBatchSummaryQuery,
    FakeDeliverablesExporter,
    FakeErrorListQuery,
    FakeLocalAuthenticator,
    FakeOutputFolderSettings,
    FakePatientDetailQuery,
)

SOLICITUD_CAPTCHA = SolicitudOperador(
    accion=AccionOperador.CAPTCHA_PORTAL_2,
    paciente=PacienteRef(
        paciente_id="P0339",
        nombre="Zambrano Lucero, Hipatia Valeria",
        cedula="1394582190",
    ),
)

SUBPAGINA_CARGA = 0
SUBPAGINA_REVISION = 1
SUBPAGINA_PROCESANDO = 2
SUBPAGINA_RESUMEN = 3


class VentanaDemo(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LuxMed UI — demo interactivo (datos simulados)")
        self._dialogos_abiertos: list[QDialog] = []
        self._ajustes = FakeOutputFolderSettings()
        self._cabecera_demo = cabecera_simulada()

        self._paginas_raiz = QStackedWidget()
        self._paginas_raiz.addWidget(self._crear_pagina_login())
        self._paginas_raiz.addWidget(self._crear_shell())

        aviso = QLabel(
            "Demo interactivo con datos simulados (fakes). Nada de esto llama a Playwright, "
            "SQLite ni al backend real."
        )
        aviso.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_etiqueta))
        aviso.setStyleSheet(f"color: {COLORES.tinta_sec};")

        boton_dialogos = QPushButton("Diálogos de prueba")
        boton_dialogos.setMenu(self._crear_menu_dialogos())

        barra_demo = QFrame()
        barra_demo.setStyleSheet(
            f"background-color: {COLORES.panel}; border-bottom: 1px solid {COLORES.filete};"
        )
        disposicion_barra_demo = QHBoxLayout(barra_demo)
        disposicion_barra_demo.setContentsMargins(
            ESPACIADO.md, ESPACIADO.xs, ESPACIADO.md, ESPACIADO.xs
        )
        disposicion_barra_demo.addWidget(aviso)
        disposicion_barra_demo.addStretch(1)
        disposicion_barra_demo.addWidget(boton_dialogos)

        contenedor = QWidget()
        disposicion = QVBoxLayout(contenedor)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(0)
        disposicion.addWidget(barra_demo)
        disposicion.addWidget(self._paginas_raiz, 1)
        self.setCentralWidget(contenedor)

    def _crear_pagina_login(self) -> QWidget:
        vista = LoginView()
        self._presenter_login = LoginPresenter(
            vista, FakeLocalAuthenticator(), self._al_iniciar_sesion
        )
        vista.intento_ingreso.connect(self._presenter_login.intentar_ingresar)
        return vista

    def _al_iniciar_sesion(self, sesion: SesionUsuario) -> None:
        self._top_bar.establecer_sesion(sesion.usuario, sesion.iniciales)
        self._paginas_raiz.setCurrentIndex(1)

    def _crear_shell(self) -> QWidget:
        self._top_bar = TopBar()
        self._top_bar.establecer_sin_lote()
        self._rail = Rail()
        self._navegacion = Navigation()

        self._navegacion.registrar(Destino.LOTE, self._crear_subpaginas_lote())
        self._navegacion.registrar(Destino.ERRORES, self._crear_pagina_errores())
        self._navegacion.registrar(Destino.AJUSTES, self._crear_pagina_ajustes())
        self._rail.destino_elegido.connect(
            lambda destino: self._navegacion.mostrar(Destino(destino))
        )
        self._rail.boton_errores.establecer_contador(
            len(FakeErrorListQuery().errores_pendientes())
        )

        cuerpo = QHBoxLayout()
        cuerpo.setContentsMargins(0, 0, 0, 0)
        cuerpo.setSpacing(0)
        cuerpo.addWidget(self._rail)
        cuerpo.addWidget(self._navegacion, 1)

        contenedor = QWidget()
        disposicion = QVBoxLayout(contenedor)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(0)
        disposicion.addWidget(self._top_bar)
        disposicion.addLayout(cuerpo, 1)
        return contenedor

    def _crear_subpaginas_lote(self) -> QWidget:
        self._subpaginas_lote = QStackedWidget()
        self._subpaginas_lote.addWidget(self._crear_pagina_carga())
        self._subpaginas_lote.addWidget(self._crear_pagina_revision())
        self._subpaginas_lote.addWidget(self._crear_pagina_procesando())
        self._subpaginas_lote.addWidget(self._crear_pagina_resumen())
        return self._subpaginas_lote

    def _crear_pagina_carga(self) -> QWidget:
        self._vista_carga = UploadView()
        self._presenter_carga = UploadPresenter(
            self._vista_carga, FakeBatchIntake(), self._al_leer_lote
        )
        self._vista_carga.archivo_elegido.connect(self._presenter_carga.archivo_elegido)
        return self._vista_carga

    def _al_leer_lote(self, preview: object) -> None:
        self._vista_revision.mostrar_preview(preview)  # type: ignore[arg-type]
        self._subpaginas_lote.setCurrentIndex(SUBPAGINA_REVISION)

    def _crear_pagina_revision(self) -> QWidget:
        self._vista_revision = ReviewView()
        self._presenter_revision = ReviewPresenter(
            self._vista_revision,
            preview_lote_simulado(),
            self._al_descartar_lote,
            self._al_iniciar_campana,
        )
        self._vista_revision.lote_descartado.connect(
            self._presenter_revision.descartar_lote
        )
        self._vista_revision.campana_iniciada.connect(
            self._presenter_revision.iniciar_campana
        )
        return self._vista_revision

    def _al_descartar_lote(self) -> None:
        self._top_bar.establecer_sin_lote()
        self._subpaginas_lote.setCurrentIndex(SUBPAGINA_CARGA)

    def _al_iniciar_campana(self) -> None:
        self._top_bar.establecer_lote(self._texto_lote(), "En curso", "proceso")
        self._subpaginas_lote.setCurrentIndex(SUBPAGINA_PROCESANDO)
        self._vista_procesando.mostrar_solicitud_login_portal3()

    def _texto_lote(self) -> str:
        return (
            f"{self._cabecera_demo.archivo} · {self._cabecera_demo.total_filas} filas"
        )

    def _crear_pagina_procesando(self) -> QWidget:
        self._vista_procesando = ProcessingView()
        self._vista_procesando.establecer_cabecera(
            cabecera_simulada(EstadoLote.EN_CURSO)
        )
        self._vista_procesando.establecer_filas(filas_paciente_simuladas())
        self._vista_procesando.actualizar_progreso(progreso_simulado())

        self._presenter_detalle = PatientDetailPresenter(
            self._vista_procesando.panel_detalle, FakePatientDetailQuery()
        )
        self._vista_procesando.paciente_seleccionado.connect(
            self._presenter_detalle.mostrar
        )
        self._vista_procesando.entregables_solicitados.connect(
            self._abrir_dialogo_entregables
        )

        barra_simulacion = QFrame()
        disposicion_barra = QHBoxLayout(barra_simulacion)
        disposicion_barra.setContentsMargins(
            ESPACIADO.md, ESPACIADO.sm, ESPACIADO.md, ESPACIADO.sm
        )
        disposicion_barra.setSpacing(ESPACIADO.sm)
        etiqueta = QLabel("Simular:")
        etiqueta.setFont(
            QFont(
                TIPOGRAFIA.familia_sans,
                TIPOGRAFIA.tamano_etiqueta,
                TIPOGRAFIA.peso_medio,
            )
        )
        disposicion_barra.addWidget(etiqueta)
        boton_login = QPushButton("Login Portal 3")
        boton_login.clicked.connect(
            self._vista_procesando.mostrar_solicitud_login_portal3
        )
        boton_captcha = QPushButton("Captcha Portal 2")
        boton_captcha.clicked.connect(
            lambda: self._vista_procesando.mostrar_solicitud_captcha(SOLICITUD_CAPTCHA)
        )
        boton_detenido = QPushButton("Lote detenido")
        boton_detenido.clicked.connect(self._al_simular_lote_detenido)
        boton_resumen = QPushButton("Ir a Resumen")
        boton_resumen.clicked.connect(self._al_simular_lote_finalizado)
        disposicion_barra.addWidget(boton_login)
        disposicion_barra.addWidget(boton_captcha)
        disposicion_barra.addWidget(boton_detenido)
        disposicion_barra.addWidget(boton_resumen)
        disposicion_barra.addStretch(1)

        contenedor = QWidget()
        disposicion = QVBoxLayout(contenedor)
        disposicion.setContentsMargins(0, 0, 0, 0)
        disposicion.setSpacing(0)
        disposicion.addWidget(barra_simulacion)
        disposicion.addWidget(self._vista_procesando, 1)
        return contenedor

    def _al_simular_lote_detenido(self) -> None:
        self._vista_procesando.establecer_cabecera(
            cabecera_simulada(EstadoLote.DETENIDO)
        )
        self._top_bar.establecer_lote(self._texto_lote(), "Detenido", "alerta")
        self._vista_procesando.mostrar_lote_detenido(resultado_detenido_simulado())

    def _al_simular_lote_finalizado(self) -> None:
        self._top_bar.establecer_lote(self._texto_lote(), "Finalizado", "exito")
        self._subpaginas_lote.setCurrentIndex(SUBPAGINA_RESUMEN)

    def _abrir_dialogo_entregables(self) -> None:
        dialogo = DeliverablesDialog(
            resumen_lote_simulado(), self._ajustes.obtener(), self
        )
        exportador = FakeDeliverablesExporter()
        dialogo.generar_solicitado.connect(
            lambda seleccion: exportador.exportar(seleccion)
        )
        dialogo.show()
        self._dialogos_abiertos.append(dialogo)

    def _crear_pagina_resumen(self) -> QWidget:
        vista = SummaryView()
        presenter = SummaryPresenter(vista, FakeBatchSummaryQuery())
        presenter.cargar()
        vista.entregables_solicitados.connect(self._abrir_dialogo_entregables)
        return vista

    def _crear_pagina_errores(self) -> QWidget:
        vista = ErrorsView()
        presenter = ErrorsPresenter(vista, FakeErrorListQuery())
        presenter.cargar()
        vista.reproceso_solicitado.connect(self._al_reintentar_errores)
        return vista

    def _al_reintentar_errores(self, ids: tuple[str, ...]) -> None:
        dialogo = Portal3LoginDialog(es_reproceso=True, parent=self)
        dialogo.show()
        self._dialogos_abiertos.append(dialogo)

    def _crear_pagina_ajustes(self) -> QWidget:
        vista = SettingsView()
        presenter = SettingsPresenter(vista, self._ajustes)
        presenter.cargar()
        vista.carpeta_elegida.connect(presenter.cambiar_carpeta)
        return vista

    def _crear_menu_dialogos(self) -> QMenu:
        menu = QMenu(self)
        opciones: tuple[tuple[str, object], ...] = (
            (
                "04 Login Portal 3 (primera vez)",
                lambda: Portal3LoginDialog(parent=self),
            ),
            (
                "04 Login Portal 3 (reproceso)",
                lambda: Portal3LoginDialog(es_reproceso=True, parent=self),
            ),
            ("06 Captcha Portal 2", lambda: CaptchaDialog(SOLICITUD_CAPTCHA, self)),
            (
                "07 Lote detenido",
                lambda: BatchStoppedDialog(resultado_detenido_simulado(), self),
            ),
            (
                "10 Generar entregables",
                lambda: DeliverablesDialog(
                    resumen_lote_simulado(), self._ajustes.obtener(), self
                ),
            ),
            (
                "Confirmar cierre con lote en curso",
                lambda: CloseConfirmationDialog(self),
            ),
        )
        for texto, fabrica in opciones:
            accion = menu.addAction(texto)
            assert accion is not None
            accion.triggered.connect(
                lambda _=False, f=fabrica: self._abrir_dialogo_suelto(f)
            )
        return menu

    def _abrir_dialogo_suelto(self, fabrica: object) -> None:
        dialogo = fabrica()  # type: ignore[operator]
        dialogo.show()
        self._dialogos_abiertos.append(dialogo)


def main() -> int:
    app = QApplication(sys.argv)
    preparar(app)
    ventana = VentanaDemo()
    ventana.resize(1440, 900)
    ventana.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
