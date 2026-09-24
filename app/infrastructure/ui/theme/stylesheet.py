from __future__ import annotations

from dataclasses import asdict
from string import Template

from PyQt6.QtWidgets import QWidget

from app.infrastructure.ui.theme.tokens import ColorTokens


def build_stylesheet(template: str, tokens: ColorTokens) -> str:
    return Template(template).substitute(asdict(tokens))


def repolish(widget: QWidget) -> None:
    estilo = widget.style()
    if estilo is not None:
        estilo.unpolish(widget)
        estilo.polish(widget)
