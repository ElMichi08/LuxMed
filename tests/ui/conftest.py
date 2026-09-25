from __future__ import annotations

import pytest
from PyQt6.QtWidgets import QApplication

from app.infrastructure.ui.theme.aplicar import aplicar_tema


@pytest.fixture(scope="session", autouse=True)
def _tema_aplicado(qapp: QApplication) -> None:
    aplicar_tema(qapp)
