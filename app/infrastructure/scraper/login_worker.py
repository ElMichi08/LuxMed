from __future__ import annotations
from PyQt6.QtCore import QThread, pyqtSignal
from app.infrastructure.scraper.portal3_adapter import Portal3Adapter


class LoginWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(
        self,
        adapter: Portal3Adapter,
        timeout_ms: int = 300000,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._adapter = adapter
        self._timeout_ms = timeout_ms

    def run(self) -> None:
        try:
            success = self._adapter.vincular_sesion_portal_3(
                timeout_ms=self._timeout_ms
            )
            if success:
                self.finished.emit(True, "Sesión del Portal 3 vinculada correctamente")
            else:
                self.finished.emit(False, "No se pudo completar el login del Portal 3")
        except Exception as e:
            self.finished.emit(False, f"Error durante el login: {e}")
