from __future__ import annotations

import io
import logging
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TextIO

CEDULA_OCULTA = "[CI oculta]"
NOMBRE_OCULTO = "[paciente]"
NUMERO_CON_FORMA_DE_CEDULA = re.compile(r"(?<!\d)\d{7,13}(?!\d)(?!\s*bytes)")


@dataclass(frozen=True, slots=True)
class IdentidadPaciente:
    etiqueta: str
    cedula: str
    nombre: str


def _patron_literal(texto: str) -> re.Pattern[str]:
    return re.compile(re.escape(texto.strip()), re.IGNORECASE)


class SanitizadorPii:
    def __init__(self) -> None:
        self._reemplazos: tuple[tuple[re.Pattern[str], str], ...] = ()

    def registrar(self, identidades: Iterable[IdentidadPaciente]) -> None:
        nombres: list[tuple[re.Pattern[str], str]] = []
        cedulas: list[tuple[re.Pattern[str], str]] = []
        for identidad in identidades:
            if len(identidad.nombre.strip()) > 2:
                nombres.append((_patron_literal(identidad.nombre), NOMBRE_OCULTO))
            if identidad.cedula.strip():
                cedulas.append((_patron_literal(identidad.cedula), identidad.etiqueta))
        nombres.sort(key=lambda par: len(par[0].pattern), reverse=True)
        cedulas.sort(key=lambda par: len(par[0].pattern), reverse=True)
        self._reemplazos = (*nombres, *cedulas)

    def limpiar(self, texto: str) -> str:
        for patron, reemplazo in self._reemplazos:
            texto = patron.sub(reemplazo, texto)
        return NUMERO_CON_FORMA_DE_CEDULA.sub(CEDULA_OCULTA, texto)


class FormatterSanitizado(logging.Formatter):
    def __init__(self, sanitizador: SanitizadorPii, formato: str) -> None:
        super().__init__(formato)
        self._sanitizador = sanitizador

    def format(self, record: logging.LogRecord) -> str:
        return self._sanitizador.limpiar(super().format(record))


class ConsolaProtegida(io.TextIOBase):
    def __init__(self, destino: TextIO | None, sanitizador: SanitizadorPii, visible: bool) -> None:
        super().__init__()
        self._destino = destino
        self._sanitizador = sanitizador
        self._visible = visible

    def writable(self) -> bool:
        return True

    def write(self, texto: str) -> int:
        if self._visible and self._destino is not None:
            self._destino.write(self._sanitizador.limpiar(texto))
        return len(texto)

    def flush(self) -> None:
        if self._destino is not None:
            self._destino.flush()


def proteger_consola(sanitizador: SanitizadorPii, mostrar_depuracion: bool) -> None:
    sys.stdout = ConsolaProtegida(sys.__stdout__, sanitizador, visible=mostrar_depuracion)
    sys.stderr = ConsolaProtegida(sys.__stderr__, sanitizador, visible=True)
