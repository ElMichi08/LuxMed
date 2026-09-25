from __future__ import annotations

import pytest

pytest.importorskip("playwright")

from app.infrastructure.scraper import portal3_adapter
from app.infrastructure.scraper.portal3_adapter import Portal3Adapter


def test_usa_credenciales_inyectadas() -> None:
    adaptador = Portal3Adapter(usuario="medico", contrasena="clave")
    assert adaptador._usuario == "medico"
    assert adaptador._contrasena == "clave"


def test_sin_inyeccion_conserva_las_del_env() -> None:
    adaptador = Portal3Adapter()
    assert adaptador._usuario == portal3_adapter.PORTAL3_USUARIO
    assert adaptador._contrasena == portal3_adapter.PORTAL3_CONTRASENA
