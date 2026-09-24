from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.application.dto import (
    AccionOperador,
    DecisionOperador,
    PacienteRef,
    SolicitudOperador,
)
from app.infrastructure.ui.dialogs.captcha_dialog import CaptchaDialog
from app.infrastructure.ui.dialogs.portal3_login_dialog import Portal3LoginDialog
from tests.ui.fakes.ports import FakeOperatorGate

SOLICITUD_CAPTCHA = SolicitudOperador(
    accion=AccionOperador.CAPTCHA_PORTAL_2,
    paciente=PacienteRef(
        paciente_id="P0339",
        nombre="Zambrano Lucero, Hipatia Valeria",
        cedula="1394582190",
    ),
)


def test_fake_operator_gate_registra_solicitudes_y_cierres() -> None:
    compuerta = FakeOperatorGate()
    compuerta.solicitar(SOLICITUD_CAPTCHA)
    compuerta.resolver_con(DecisionOperador.REINTENTAR_CAPTCHA)

    assert compuerta.solicitudes == [SOLICITUD_CAPTCHA]
    assert (
        compuerta.esperar(AccionOperador.CAPTCHA_PORTAL_2, lambda: False)
        == DecisionOperador.REINTENTAR_CAPTCHA
    )

    compuerta.cerrar(AccionOperador.CAPTCHA_PORTAL_2)
    assert compuerta.cierres == [AccionOperador.CAPTCHA_PORTAL_2]


def test_captcha_dialog_reintentar_emite_decision() -> None:
    dialogo = CaptchaDialog(SOLICITUD_CAPTCHA)
    decisiones: list[DecisionOperador] = []
    dialogo.decision_tomada.connect(decisiones.append)

    dialogo.boton_reintentar.click()

    assert decisiones == [DecisionOperador.REINTENTAR_CAPTCHA]


def test_captcha_dialog_marcar_error_emite_decision() -> None:
    dialogo = CaptchaDialog(SOLICITUD_CAPTCHA)
    decisiones: list[DecisionOperador] = []
    dialogo.decision_tomada.connect(decisiones.append)

    dialogo.boton_marcar_error.click()

    assert decisiones == [DecisionOperador.MARCAR_ERROR_PORTAL_2]


def test_captura_dialogo_login_portal3(capturar: Callable[..., Path]) -> None:
    dialogo = Portal3LoginDialog()
    tamano = dialogo.sizeHint()
    ruta = capturar(dialogo, "dialogo_login_portal3", tamano.width(), tamano.height())
    assert ruta.exists()


def test_captura_dialogo_login_portal3_reproceso(capturar: Callable[..., Path]) -> None:
    dialogo = Portal3LoginDialog(es_reproceso=True)
    tamano = dialogo.sizeHint()
    ruta = capturar(
        dialogo, "dialogo_login_portal3_reproceso", tamano.width(), tamano.height()
    )
    assert ruta.exists()


def test_dialogo_login_portal3_reproceso_omite_nota_de_campana() -> None:
    dialogo = Portal3LoginDialog(es_reproceso=True)

    assert dialogo._nota is None


def test_dialogo_login_portal3_primera_vez_muestra_nota_de_campana() -> None:
    dialogo = Portal3LoginDialog()

    assert dialogo._nota is not None
    assert "La campaña comenzará automáticamente" in dialogo._nota.text()


def test_captura_dialogo_captcha(capturar: Callable[..., Path]) -> None:
    dialogo = CaptchaDialog(SOLICITUD_CAPTCHA)
    tamano = dialogo.sizeHint()
    ruta = capturar(dialogo, "dialogo_captcha", tamano.width(), tamano.height())
    assert ruta.exists()
