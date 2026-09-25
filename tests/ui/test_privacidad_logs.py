from __future__ import annotations

import io
import logging
from pathlib import Path

from pytestqt.qtbot import QtBot

from app.infrastructure.ui.log_bridge import (
    ArchivoLogLote,
    EmisorLog,
    LineaLog,
    QtLogHandler,
)
from app.infrastructure.ui.privacidad_logs import (
    CEDULA_OCULTA,
    NOMBRE_OCULTO,
    ConsolaProtegida,
    IdentidadPaciente,
    SanitizadorPii,
)

CEDULA = "1400303796"
NOMBRE = "JUA YURANGUI ALISIA FLORA"


def _sanitizador() -> SanitizadorPii:
    sanitizador = SanitizadorPii()
    sanitizador.registrar([IdentidadPaciente("Fila 0004", CEDULA, NOMBRE)])
    return sanitizador


def test_reemplaza_cedula_y_nombre_conocidos() -> None:
    texto = _sanitizador().limpiar(f"Procesando paciente {CEDULA} ({NOMBRE})")
    assert texto == f"Procesando paciente Fila 0004 ({NOMBRE_OCULTO})"


def test_nombre_sin_distinguir_mayusculas_y_dentro_de_rutas() -> None:
    texto = _sanitizador().limpiar(rf"PDF guardado: C:\salidas\{CEDULA}_Jua Yurangui Alisia Flora_REPORT.pdf")
    assert CEDULA not in texto
    assert "Yurangui" not in texto


def test_oculta_cedulas_desconocidas_como_la_del_titular() -> None:
    texto = SanitizadorPii().limpiar("Acreditador encontrado: 0998887776 · CI=17124981")
    assert texto == f"Acreditador encontrado: {CEDULA_OCULTA} · CI={CEDULA_OCULTA}"


def test_no_oculta_tamanos_ni_numeros_cortos() -> None:
    texto = SanitizadorPii().limpiar("Portal 3 OK, pdf: 1234567 bytes · intento 2 · 3800ms")
    assert texto == "Portal 3 OK, pdf: 1234567 bytes · intento 2 · 3800ms"


def test_handler_de_la_ui_emite_mensajes_sanitizados(qtbot: QtBot) -> None:
    emisor = EmisorLog()
    recibidas: list[LineaLog] = []
    emisor.linea.connect(recibidas.append)
    registro = logging.LogRecord("app.application.orchestrator", logging.INFO, __file__, 1, "Paciente %s (%s)", (CEDULA, NOMBRE), None)
    QtLogHandler(emisor, _sanitizador()).emit(registro)
    assert recibidas[0].mensaje == f"Paciente Fila 0004 ({NOMBRE_OCULTO})"


def test_archivo_de_lote_no_guarda_pii_ni_en_trazas(tmp_path: Path) -> None:
    archivo = ArchivoLogLote(tmp_path, _sanitizador())
    ruta = archivo.abrir("2026-09-25-01")
    registro_logger = logging.getLogger("prueba.privacidad")
    registro_logger.setLevel(logging.INFO)
    try:
        raise RuntimeError(f"Timeout consultando {CEDULA}")
    except RuntimeError:
        registro_logger.exception("Error procesando paciente %s (%s)", CEDULA, NOMBRE)
    archivo.cerrar()
    contenido = ruta.read_text(encoding="utf-8")
    assert CEDULA not in contenido
    assert NOMBRE not in contenido
    assert "Fila 0004" in contenido


def test_consola_oculta_depuracion_por_defecto() -> None:
    destino = io.StringIO()
    consola = ConsolaProtegida(destino, _sanitizador(), visible=False)
    print(f"[DEBUG] PDF línea 3: '{NOMBRE} {CEDULA}'", file=consola)
    assert destino.getvalue() == ""


def test_consola_de_depuracion_sale_sanitizada() -> None:
    destino = io.StringIO()
    consola = ConsolaProtegida(destino, _sanitizador(), visible=True)
    print(f"[DEBUG] PDF línea 3: '{NOMBRE} {CEDULA}' titular 0998887776", file=consola)
    salida = destino.getvalue()
    assert CEDULA not in salida and NOMBRE not in salida and "0998887776" not in salida
    assert "Fila 0004" in salida
