from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette

from app.infrastructure.ui.theme.tokens import ColorTokens


def build_palette(tokens: ColorTokens) -> QPalette:
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: tokens.lienzo,
        QPalette.ColorRole.WindowText: tokens.tinta,
        QPalette.ColorRole.Base: tokens.blanco,
        QPalette.ColorRole.AlternateBase: tokens.panel,
        QPalette.ColorRole.Text: tokens.tinta,
        QPalette.ColorRole.Button: tokens.boton,
        QPalette.ColorRole.ButtonText: tokens.tinta,
        QPalette.ColorRole.Highlight: tokens.indigo_suave,
        QPalette.ColorRole.HighlightedText: tokens.tinta,
        QPalette.ColorRole.ToolTipBase: tokens.tinta,
        QPalette.ColorRole.ToolTipText: tokens.blanco,
        QPalette.ColorRole.PlaceholderText: tokens.tinta_ter,
    }
    for rol, color in roles.items():
        palette.setColor(rol, QColor(color))
    for rol in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(QPalette.ColorGroup.Disabled, rol, QColor(tokens.tinta_ter))
    return palette
