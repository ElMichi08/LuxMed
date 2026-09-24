from __future__ import annotations

from PyQt6.QtGui import QColor, QPalette

from app.infrastructure.ui.theme.tokens import ColorTokens


def build_palette(tokens: ColorTokens) -> QPalette:
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(tokens.lienzo))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(tokens.tinta))
    palette.setColor(QPalette.ColorRole.Base, QColor(tokens.blanco))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(tokens.panel))
    palette.setColor(QPalette.ColorRole.Text, QColor(tokens.tinta))
    palette.setColor(QPalette.ColorRole.Button, QColor(tokens.panel))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(tokens.tinta))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(tokens.indigo))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(tokens.blanco))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(tokens.tinta))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(tokens.blanco))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(tokens.tinta_ter))
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        QColor(tokens.tinta_ter),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(tokens.tinta_ter)
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColor(tokens.tinta_ter),
    )
    return palette
