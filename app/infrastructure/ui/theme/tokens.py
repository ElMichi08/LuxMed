from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ColorTokens:
    lienzo: str = "#E6E6E2"
    panel: str = "#FAFAF8"
    blanco: str = "#FFFFFF"
    filete: str = "#C9C9C3"
    filete_suave: str = "#DCDCD7"
    filete_celda: str = "#F0EFEB"
    cabecera: str = "#DEDEDA"
    boton: str = "#EAEAE6"
    boton_presionado: str = "#C9C9C3"
    fila_hover: str = "#F7F6F7"
    fila_total: str = "#F2F2EE"
    campo_lectura: str = "#F0EFEB"
    tinta: str = "#1A1A18"
    tinta_hover: str = "#333330"
    tinta_sec: str = "#555550"
    tinta_ter: str = "#84847E"
    indigo: str = "#4B3F72"
    indigo_suave: str = "#EDEAF3"
    indigo_borde: str = "#DDD8E8"
    verde: str = "#1F6B4A"
    verde_fondo: str = "#E8F5E9"
    verde_borde: str = "#C8E6C9"
    rojo: str = "#A3231D"
    rojo_fondo: str = "#FDEDEC"
    rojo_borde: str = "#F5C2C0"
    velo: str = "#801A1A18"


@dataclass(frozen=True, slots=True)
class TypographyTokens:
    sans: str = "Archivo"
    narrow: str = "Archivo Narrow"
    mono: str = "IBM Plex Mono"
    micro: int = 9
    chip: int = 10
    etiqueta: int = 11
    base: int = 12
    cuerpo: int = 13
    subtitulo: int = 14
    titulo: int = 16
    titulo_grande: int = 20
    cifra: int = 24
    cifra_grande: int = 28


@dataclass(frozen=True, slots=True)
class GeometryTokens:
    barra_superior: int = 48
    riel_ancho: int = 64
    riel_item: int = 60
    barra_estado: int = 28
    barra_filtros: int = 46
    pie_acciones: int = 52
    fila: int = 40
    cabecera_tabla: int = 34
    boton: int = 32
    campo: int = 32
    radio: int = 3


COLORES = ColorTokens()
TIPOGRAFIA = TypographyTokens()
GEOMETRIA = GeometryTokens()
