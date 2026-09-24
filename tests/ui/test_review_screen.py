from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.application.dto import PreviewLote
from app.infrastructure.ui.presenters.review_presenter import ReviewPresenter
from app.infrastructure.ui.screens.review_view import ReviewView
from tests.ui.fakes.dataset import preview_lote_simulado


class VistaReviewFalsa:
    def __init__(self) -> None:
        self.preview_mostrado: PreviewLote | None = None

    def mostrar_preview(self, preview: PreviewLote) -> None:
        self.preview_mostrado = preview


def test_review_presenter_muestra_preview_al_construirse() -> None:
    vista = VistaReviewFalsa()
    preview = preview_lote_simulado()

    ReviewPresenter(vista, preview, lambda: None, lambda: None)

    assert vista.preview_mostrado == preview


def test_review_presenter_descartar_llama_callback() -> None:
    vista = VistaReviewFalsa()
    descartes: list[None] = []
    presenter = ReviewPresenter(
        vista, preview_lote_simulado(), lambda: descartes.append(None), lambda: None
    )

    presenter.descartar_lote()

    assert len(descartes) == 1


def test_review_presenter_iniciar_llama_callback() -> None:
    vista = VistaReviewFalsa()
    inicios: list[None] = []
    presenter = ReviewPresenter(
        vista, preview_lote_simulado(), lambda: None, lambda: inicios.append(None)
    )

    presenter.iniciar_campana()

    assert len(inicios) == 1


def test_review_view_cambia_tabla_al_cambiar_pestana() -> None:
    vista = ReviewView()
    preview = preview_lote_simulado()
    vista.mostrar_preview(preview)

    assert vista._modelo.rowCount() == len(preview.listos)

    vista._boton_descartados.setChecked(True)
    assert vista._modelo.rowCount() == len(preview.descartados)

    vista._boton_listos.setChecked(True)
    assert vista._modelo.rowCount() == len(preview.listos)


def test_captura_review_pestana_listos(capturar: Callable[..., Path]) -> None:
    vista = ReviewView()
    vista.mostrar_preview(preview_lote_simulado())
    ruta = capturar(vista, "review_listos")
    assert ruta.exists()


def test_captura_review_pestana_descartados(capturar: Callable[..., Path]) -> None:
    vista = ReviewView()
    vista.mostrar_preview(preview_lote_simulado())
    vista._boton_descartados.setChecked(True)
    ruta = capturar(vista, "review_descartados")
    assert ruta.exists()
