from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

FORMATO_ARCHIVO = "[%(asctime)s] %(levelname)-5s [%(name)s] %(message)s"

ORIGENES = (
    ("portal_1", "Portal 1"),
    ("playwright_scraper", "Portal 1"),
    ("portal2", "Portal 2"),
    ("altcha", "Portal 2"),
    ("portal3", "Portal 3"),
    ("orchestrator", "Orquestador"),
    ("lote_service", "Lote"),
    ("excel", "Excel"),
    ("pdf", "PDF"),
    ("retry", "Reintentos"),
)


def origen_legible(nombre_logger: str) -> str:
    for fragmento, origen in ORIGENES:
        if fragmento in nombre_logger:
            return origen
    return nombre_logger.rsplit(".", 1)[-1]


@dataclass(frozen=True, slots=True)
class LineaLog:
    hora: datetime
    nivel: int
    origen: str
    mensaje: str

    @property
    def nombre_nivel(self) -> str:
        return logging.getLevelName(self.nivel)[:5]

    @property
    def texto_hora(self) -> str:
        return self.hora.strftime("%H:%M:%S.") + f"{self.hora.microsecond // 1000:03d}"

    @property
    def texto_plano(self) -> str:
        return f"[{self.texto_hora}]  {self.nombre_nivel:<5}  [{self.origen}]  {self.mensaje}"

    @property
    def resumen(self) -> str:
        return f"{self.hora:%H:%M:%S} {self.origen} · {self.mensaje}"


class EmisorLog(QObject):
    linea = pyqtSignal(object)


class QtLogHandler(logging.Handler):
    def __init__(self, emisor: EmisorLog) -> None:
        super().__init__(logging.INFO)
        self._emisor = emisor

    def emit(self, record: logging.LogRecord) -> None:
        try:
            mensaje = record.getMessage()
        except Exception:
            mensaje = str(record.msg)
        self._emisor.linea.emit(
            LineaLog(
                hora=datetime.fromtimestamp(record.created),
                nivel=record.levelno,
                origen=origen_legible(record.name),
                mensaje=mensaje.splitlines()[0] if mensaje else "",
            )
        )


class ArchivoLogLote:
    def __init__(self, carpeta: Path) -> None:
        self._carpeta = carpeta
        self._handler: logging.FileHandler | None = None
        self.ruta: Path | None = None

    def abrir(self, lote_id: str) -> Path:
        self.cerrar()
        self._carpeta.mkdir(parents=True, exist_ok=True)
        self.ruta = self._carpeta / f"lote_{lote_id}.log"
        self._handler = logging.FileHandler(self.ruta, encoding="utf-8")
        self._handler.setFormatter(logging.Formatter(FORMATO_ARCHIVO))
        self._handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(self._handler)
        return self.ruta

    def cerrar(self) -> None:
        if self._handler is None:
            return
        logging.getLogger().removeHandler(self._handler)
        self._handler.close()
        self._handler = None


def instalar_puente(emisor: EmisorLog) -> QtLogHandler:
    raiz = logging.getLogger()
    if raiz.level > logging.INFO or raiz.level == logging.NOTSET:
        raiz.setLevel(logging.INFO)
    handler = QtLogHandler(emisor)
    raiz.addHandler(handler)
    return handler
