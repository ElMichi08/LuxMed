from __future__ import annotations

from pathlib import Path

import pytest

from app.domain.entities import CredencialesPortal3
from app.infrastructure.config.env_configuracion import EnvConfiguracionAdapter


def test_valores_por_defecto_sin_env(tmp_path: Path) -> None:
    adaptador = EnvConfiguracionAdapter(tmp_path / ".env", tmp_path / "salidas")
    assert adaptador.obtener_carpeta_salida() == str(tmp_path / "salidas")
    assert adaptador.obtener_credenciales_portal3().completas is False


def test_ida_y_vuelta_conserva_otras_claves(tmp_path: Path) -> None:
    ruta_env = tmp_path / ".env"
    ruta_env.write_text("STITCH_API_KEY=abc\n", encoding="utf-8")
    adaptador = EnvConfiguracionAdapter(ruta_env, tmp_path)
    adaptador.guardar_credenciales_portal3(CredencialesPortal3(" medico ", "cl@ve'#ñ"))
    adaptador.guardar_carpeta_salida(r"D:\LuxMed\salidas")
    assert adaptador.obtener_credenciales_portal3() == CredencialesPortal3("medico", "cl@ve'#ñ")
    assert adaptador.obtener_carpeta_salida() == r"D:\LuxMed\salidas"
    assert "STITCH_API_KEY=abc" in ruta_env.read_text(encoding="utf-8")


def test_portal3_lee_las_mismas_claves(tmp_path: Path) -> None:
    dotenv = pytest.importorskip("dotenv")
    ruta_env = tmp_path / ".env"
    EnvConfiguracionAdapter(ruta_env, tmp_path).guardar_credenciales_portal3(CredencialesPortal3("medico", "clave"))
    valores = dotenv.dotenv_values(ruta_env, encoding="utf-8")
    assert valores["usuario"] == "medico"
    assert valores["contraseña"] == "clave"
