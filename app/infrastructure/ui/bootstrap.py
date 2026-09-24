from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from app.infrastructure.ui.shell.main_window import MainWindow
from app.infrastructure.ui.theme.fonts import load_fonts
from app.infrastructure.ui.theme.palette import build_palette
from app.infrastructure.ui.theme.stylesheet import build_stylesheet
from app.infrastructure.ui.theme.tokens import COLORES, TIPOGRAFIA

UI_DIR = Path(__file__).resolve().parent
FUENTES_DIR = UI_DIR / "assets" / "fonts"
PLANTILLA_QSS = UI_DIR / "theme" / "luxmed.qss.tpl"


def preparar(app: QApplication) -> None:
    app.setStyle("Fusion")
    load_fonts(FUENTES_DIR)
    app.setFont(QFont(TIPOGRAFIA.familia_sans, TIPOGRAFIA.tamano_base))
    app.setPalette(build_palette(COLORES))
    app.setStyleSheet(
        build_stylesheet(PLANTILLA_QSS.read_text(encoding="utf-8"), COLORES)
    )


def ejecutar() -> int:
    app = QApplication(sys.argv)
    preparar(app)
    ventana = MainWindow()
    ventana.resize(1280, 800)
    ventana.show()
    return app.exec()
