from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QFontDatabase


def load_fonts(directory: Path) -> list[str]:
    families: list[str] = []
    for font_file in sorted(directory.rglob("*.ttf")):
        font_id = QFontDatabase.addApplicationFont(str(font_file))
        if font_id != -1:
            families.extend(QFontDatabase.applicationFontFamilies(font_id))
    return families
