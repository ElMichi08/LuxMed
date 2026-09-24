from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from app.application.dto import EstadoPaciente, EstadoPaso, RutaPortales
from app.infrastructure.ui.theme.stylesheet import repolish
from app.infrastructure.ui.theme.tokens import COLORES
from app.infrastructure.ui.widgets.card import Card
from app.infrastructure.ui.widgets.dropzone import DropZone
from app.infrastructure.ui.widgets.empty_state import EmptyState
from app.infrastructure.ui.widgets.kpi_tile import KpiTile
from app.infrastructure.ui.widgets.route_dots import RouteDots
from app.infrastructure.ui.widgets.status_chip import StatusChip


def test_captura_card(capturar: Callable[..., Path]) -> None:
    tarjeta = Card("Qué se lee del archivo")
    tarjeta.agregar(QLabel("Columnas leídas: nombre, cédula, fecha de nacimiento."))
    ruta = capturar(tarjeta, "card", 420, 140)
    assert ruta.exists()


def test_captura_status_chips_todos_los_tonos(capturar: Callable[..., Path]) -> None:
    contenedor = QWidget()
    disposicion = QHBoxLayout(contenedor)
    for estado in EstadoPaciente:
        chip = StatusChip(estado)
        disposicion.addWidget(chip)
    ruta = capturar(contenedor, "status_chip_todos", 900, 60)
    assert ruta.exists()


def test_captura_kpi_tiles(capturar: Callable[..., Path]) -> None:
    contenedor = QWidget()
    disposicion = QHBoxLayout(contenedor)
    disposicion.setSpacing(0)

    total = KpiTile("Total lote")
    total.establecer_valor(428)

    completados = KpiTile("Completados")
    completados.establecer_valor(296)
    completados.establecer_color_valor(COLORES.verde)

    invalidos = KpiTile("Inválidos")
    invalidos.establecer_valor(94)
    invalidos.establecer_color_valor(COLORES.rojo)

    en_proceso = KpiTile("En proceso")
    en_proceso.establecer_valor(1)
    en_proceso.establecer_color_valor(COLORES.indigo)
    en_proceso.establecer_activo(True)

    con_error = KpiTile("Con error")
    con_error.establecer_valor(4)
    con_error.establecer_color_valor(COLORES.rojo)

    for tile in (total, completados, invalidos, en_proceso, con_error):
        disposicion.addWidget(tile)

    ruta = capturar(contenedor, "kpi_tiles", 900, 72)
    assert ruta.exists()


def test_captura_route_dots_variantes(capturar: Callable[..., Path]) -> None:
    contenedor = QWidget()
    disposicion = QHBoxLayout(contenedor)
    disposicion.setSpacing(24)

    rutas = (
        RutaPortales(EstadoPaso.RESUELTO, EstadoPaso.RESUELTO, EstadoPaso.RESUELTO),
        RutaPortales(EstadoPaso.RESUELTO, EstadoPaso.OMITIDO, EstadoPaso.RESUELTO),
        RutaPortales(EstadoPaso.RESUELTO, EstadoPaso.EN_CURSO, EstadoPaso.PENDIENTE),
        RutaPortales(EstadoPaso.PENDIENTE, EstadoPaso.PENDIENTE, EstadoPaso.PENDIENTE),
        RutaPortales(EstadoPaso.FALLIDO, EstadoPaso.PENDIENTE, EstadoPaso.PENDIENTE),
        RutaPortales(EstadoPaso.RESUELTO, EstadoPaso.RESUELTO, EstadoPaso.FALLIDO),
    )
    for ruta in rutas:
        disposicion.addWidget(RouteDots(ruta))

    ruta_captura = capturar(contenedor, "route_dots_variantes", 500, 40)
    assert ruta_captura.exists()


def test_captura_dropzone_estados(capturar: Callable[..., Path]) -> None:
    contenedor = QWidget()
    disposicion = QHBoxLayout(contenedor)

    normal = DropZone()

    arrastrando = DropZone()
    arrastrando.setProperty("arrastrando", True)
    repolish(arrastrando)

    cargando = DropZone()
    cargando.establecer_cargando("Leyendo archivo…")

    for widget in (normal, arrastrando, cargando):
        disposicion.addWidget(widget)

    ruta = capturar(contenedor, "dropzone_estados", 1200, 260)
    assert ruta.exists()


def test_captura_empty_state(capturar: Callable[..., Path]) -> None:
    estado_vacio = EmptyState(
        "warning",
        "No hay errores pendientes",
        "Todos los pacientes se procesaron sin fallas.",
    )
    ruta = capturar(estado_vacio, "empty_state", 480, 220)
    assert ruta.exists()


def test_route_dots_tooltip_describe_los_pasos() -> None:
    ruta = RutaPortales(EstadoPaso.RESUELTO, EstadoPaso.OMITIDO, EstadoPaso.FALLIDO)
    widget = RouteDots(ruta)
    assert "P1: Hecho" in widget.toolTip()
    assert "P2: Omitido" in widget.toolTip()
    assert "P3: Fallido" in widget.toolTip()


def test_dropzone_establecer_cargando_deshabilita() -> None:
    dropzone = DropZone()
    dropzone.establecer_cargando("Leyendo archivo…")
    assert not dropzone.isEnabled()
    dropzone.establecer_cargando(None)
    assert dropzone.isEnabled()
