from __future__ import annotations

from collections.abc import Callable

from app.application.dto import SesionUsuario
from app.application.ui_ports import ILocalAuthenticator
from app.infrastructure.ui.presenters.contracts import ILoginView

MENSAJE_CREDENCIALES_INVALIDAS = "Usuario o contraseña incorrectos"


class LoginPresenter:
    def __init__(
        self,
        vista: ILoginView,
        autenticador: ILocalAuthenticator,
        al_iniciar_sesion: Callable[[SesionUsuario], None],
    ) -> None:
        self._vista = vista
        self._autenticador = autenticador
        self._al_iniciar_sesion = al_iniciar_sesion

    def intentar_ingresar(self) -> None:
        self._vista.limpiar_error()
        usuario = self._vista.usuario().strip()
        contrasena = self._vista.contrasena()
        if not usuario or not contrasena:
            self._vista.mostrar_error(MENSAJE_CREDENCIALES_INVALIDAS)
            return
        self._vista.establecer_cargando(True)
        sesion = self._autenticador.autenticar(usuario, contrasena)
        self._vista.establecer_cargando(False)
        if sesion is None:
            self._vista.mostrar_error(MENSAJE_CREDENCIALES_INVALIDAS)
            return
        self._al_iniciar_sesion(sesion)
