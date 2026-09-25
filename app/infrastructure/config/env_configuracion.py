from __future__ import annotations

from pathlib import Path

from dotenv import dotenv_values, set_key

from app.domain.entities import CredencialesPortal3
from app.domain.ports import IConfiguracionRepository

CLAVE_USUARIO = "usuario"
CLAVE_CONTRASENA = "contraseña"
CLAVE_CARPETA_SALIDA = "LUXMED_CARPETA_SALIDA"


class EnvConfiguracionAdapter(IConfiguracionRepository):
    def __init__(self, ruta_env: Path, carpeta_salida_por_defecto: Path) -> None:
        self._ruta_env = ruta_env
        self._carpeta_por_defecto = carpeta_salida_por_defecto

    def obtener_carpeta_salida(self) -> str:
        return self._leer(CLAVE_CARPETA_SALIDA) or str(self._carpeta_por_defecto)

    def guardar_carpeta_salida(self, ruta: str) -> None:
        self._escribir(CLAVE_CARPETA_SALIDA, ruta)

    def obtener_credenciales_portal3(self) -> CredencialesPortal3:
        return CredencialesPortal3(
            usuario=self._leer(CLAVE_USUARIO), contrasena=self._leer(CLAVE_CONTRASENA)
        )

    def guardar_credenciales_portal3(self, credenciales: CredencialesPortal3) -> None:
        self._escribir(CLAVE_USUARIO, credenciales.usuario.strip())
        self._escribir(CLAVE_CONTRASENA, credenciales.contrasena)

    def _leer(self, clave: str) -> str:
        if not self._ruta_env.is_file():
            return ""
        return dotenv_values(self._ruta_env, encoding="utf-8").get(clave) or ""

    def _escribir(self, clave: str, valor: str) -> None:
        self._ruta_env.parent.mkdir(parents=True, exist_ok=True)
        self._ruta_env.touch(exist_ok=True)
        set_key(self._ruta_env, clave, valor, encoding="utf-8")
