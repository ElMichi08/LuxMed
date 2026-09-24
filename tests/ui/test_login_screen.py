from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.application.dto import SesionUsuario
from app.infrastructure.ui.presenters.login_presenter import (
    MENSAJE_CREDENCIALES_INVALIDAS,
    LoginPresenter,
)
from app.infrastructure.ui.screens.login_view import LoginView
from tests.ui.fakes.ports import FakeLocalAuthenticator


class VistaLoginFalsa:
    def __init__(self, usuario: str = "", contrasena: str = "") -> None:
        self._usuario = usuario
        self._contrasena = contrasena
        self.errores: list[str] = []
        self.cargando_historial: list[bool] = []
        self.error_limpiado = False

    def usuario(self) -> str:
        return self._usuario

    def contrasena(self) -> str:
        return self._contrasena

    def mostrar_error(self, mensaje: str) -> None:
        self.errores.append(mensaje)

    def limpiar_error(self) -> None:
        self.error_limpiado = True

    def establecer_cargando(self, cargando: bool) -> None:
        self.cargando_historial.append(cargando)


def test_login_presenter_credenciales_validas_inicia_sesion() -> None:
    vista = VistaLoginFalsa("admision.01", "lux2026")
    sesiones: list[SesionUsuario] = []
    presenter = LoginPresenter(vista, FakeLocalAuthenticator(), sesiones.append)

    presenter.intentar_ingresar()

    assert len(sesiones) == 1
    assert sesiones[0].usuario == "admision.01"
    assert vista.errores == []
    assert vista.cargando_historial == [True, False]


def test_login_presenter_credenciales_invalidas_muestra_error() -> None:
    vista = VistaLoginFalsa("admision.01", "incorrecta")
    sesiones: list[SesionUsuario] = []
    presenter = LoginPresenter(vista, FakeLocalAuthenticator(), sesiones.append)

    presenter.intentar_ingresar()

    assert sesiones == []
    assert vista.errores == [MENSAJE_CREDENCIALES_INVALIDAS]


def test_login_presenter_campos_vacios_no_consulta_autenticador() -> None:
    vista = VistaLoginFalsa("", "")
    autenticador = FakeLocalAuthenticator()
    presenter = LoginPresenter(vista, autenticador, lambda _sesion: None)

    presenter.intentar_ingresar()

    assert vista.errores == [MENSAJE_CREDENCIALES_INVALIDAS]
    assert vista.cargando_historial == []


def test_captura_login_vacio(capturar: Callable[..., Path]) -> None:
    vista = LoginView()
    ruta = capturar(vista, "login_vacio")
    assert ruta.exists()


def test_captura_login_con_error(capturar: Callable[..., Path]) -> None:
    vista = LoginView()
    vista.mostrar_error(MENSAJE_CREDENCIALES_INVALIDAS)
    ruta = capturar(vista, "login_con_error")
    assert ruta.exists()


def test_captura_login_cargando(capturar: Callable[..., Path]) -> None:
    vista = LoginView()
    vista.establecer_cargando(True)
    ruta = capturar(vista, "login_cargando")
    assert ruta.exists()


def test_login_view_emite_senal_al_pulsar_entrar(capturar: Callable[..., Path]) -> None:
    vista = LoginView()
    capturar(vista, "login_para_click")
    disparos: list[None] = []
    vista.intento_ingreso.connect(lambda: disparos.append(None))
    vista._boton_entrar.click()
    assert len(disparos) == 1
