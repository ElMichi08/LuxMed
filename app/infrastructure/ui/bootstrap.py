from __future__ import annotations

import getpass
import os
import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from app.application.lote_service import ServicioLote
from app.domain.ports import IConfiguracionRepository
from app.infrastructure.ui.log_bridge import EmisorLog, instalar_puente
from app.infrastructure.ui.privacidad_logs import SanitizadorPii, proteger_consola
from app.infrastructure.ui.shell.lote_controller import LoteController
from app.infrastructure.ui.shell.main_window import MainWindow
from app.infrastructure.ui.theme.aplicar import aplicar_tema
from app.infrastructure.ui.theme.logo import icono_app, registrar_id_barra_de_tareas

VERSION_APP = "v2.4"
VARIABLE_CONSOLA_DEBUG = "LUXMED_CONSOLA_DEBUG"


def ejecutar(servicio: ServicioLote, configuracion: IConfiguracionRepository, carpeta_logs: Path) -> int:
    registrar_id_barra_de_tareas()
    app = QApplication.instance() or QApplication(sys.argv)
    assert isinstance(app, QApplication)
    app.setApplicationName("LuxMed")
    aplicar_tema(app)
    app.setWindowIcon(icono_app())
    emisor = EmisorLog()
    sanitizador = SanitizadorPii()
    proteger_consola(sanitizador, os.environ.get(VARIABLE_CONSOLA_DEBUG) == "1")
    instalar_puente(emisor, sanitizador)
    ventana = MainWindow(getpass.getuser(), VERSION_APP)
    LoteController(servicio, configuracion, ventana, emisor, carpeta_logs, sanitizador)
    ventana.show()
    return app.exec()
