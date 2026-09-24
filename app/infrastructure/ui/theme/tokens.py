from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ColorTokens:
    lienzo: str = "#E6E6E2"
    panel: str = "#FAFAF8"
    blanco: str = "#FFFFFF"
    filete: str = "#C9C9C3"
    filete_suave: str = "#DCDCD7"
    tinta: str = "#1A1A18"
    tinta_sec: str = "#555550"
    tinta_ter: str = "#8E8E88"
    indigo: str = "#4B3F72"
    indigo_suave: str = "#EDEAF3"
    indigo_borde: str = "#D5D0E3"
    verde: str = "#1F6B4A"
    verde_fondo: str = "#E8F5E9"
    verde_borde: str = "#C8E6C9"
    rojo: str = "#A3231D"
    rojo_fondo: str = "#FDEDEC"
    rojo_borde: str = "#F5C2C0"


@dataclass(frozen=True, slots=True)
class SpacingTokens:
    unidad: int = 4
    xxs: int = 2
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 20
    xxl: int = 24
    xxxl: int = 32


@dataclass(frozen=True, slots=True)
class TypographyTokens:
    familia_sans: str = "Archivo"
    familia_narrow: str = "Archivo Narrow"
    familia_mono: str = "IBM Plex Mono"
    peso_regular: int = 400
    peso_medio: int = 500
    peso_semibold: int = 600
    peso_bold: int = 700
    tamano_micro: int = 9
    tamano_chip: int = 10
    tamano_etiqueta: int = 11
    tamano_base: int = 12
    tamano_subtitulo: int = 14
    tamano_titulo: int = 16
    tamano_titulo_grande: int = 20
    tamano_cifra: int = 24
    tracking_ajustado_em: float = -0.025
    tracking_amplio_em: float = 0.05


@dataclass(frozen=True, slots=True)
class GeometryTokens:
    riel_ancho: int = 64
    fila_alto: int = 40
    borde_ancho: int = 1
    radio: int = 4
    radio_chip: int = 0


COLORES = ColorTokens()
ESPACIADO = SpacingTokens()
TIPOGRAFIA = TypographyTokens()
GEOMETRIA = GeometryTokens()
