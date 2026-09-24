from __future__ import annotations

from collections.abc import Callable

from app.application.dto import PreviewLote
from app.infrastructure.ui.presenters.contracts import IReviewView


class ReviewPresenter:
    def __init__(
        self,
        vista: IReviewView,
        preview: PreviewLote,
        al_descartar: Callable[[], None],
        al_iniciar: Callable[[], None],
    ) -> None:
        self._vista = vista
        self._al_descartar = al_descartar
        self._al_iniciar = al_iniciar
        self._vista.mostrar_preview(preview)

    def descartar_lote(self) -> None:
        self._al_descartar()

    def iniciar_campana(self) -> None:
        self._al_iniciar()
