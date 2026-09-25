from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QApplication, QStyleFactory

from app.infrastructure.ui.theme.fonts import load_fonts
from app.infrastructure.ui.theme.fuentes import fuente
from app.infrastructure.ui.theme.palette import build_palette
from app.infrastructure.ui.theme.stylesheet import build_stylesheet
from app.infrastructure.ui.theme.tokens import COLORES

UI_DIR = Path(__file__).resolve().parent.parent
PLANTILLA_QSS = Path(__file__).resolve().parent / "luxmed.qss.tpl"


def aplicar_tema(app: QApplication) -> None:
    load_fonts(UI_DIR / "assets" / "fonts")
    estilo = QStyleFactory.create("Fusion")
    if estilo is not None:
        app.setStyle(estilo)
    app.setPalette(build_palette(COLORES))
    app.setFont(fuente())
    app.setStyleSheet(build_stylesheet(PLANTILLA_QSS.read_text(encoding="utf-8"), COLORES))
