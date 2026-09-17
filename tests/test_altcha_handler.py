from unittest.mock import MagicMock, patch, PropertyMock
import pytest
from app.infrastructure.scraper.altcha_handler import AltchaHandler


@pytest.fixture
def handler():
    return AltchaHandler(max_intentos=3, pausa_manual_sec=5)


@pytest.fixture
def page():
    return MagicMock()


class TestAltchaHandlerAutoResuelto:
    def test_sin_widget_retorna_true(self, handler, page):
        page.wait_for_selector.side_effect = Exception("not found")
        result = handler.esperar_y_resolver(page)
        assert result is True

    def test_callback_devuelve_token(self, handler, page):
        page.wait_for_selector.return_value = MagicMock()
        page.evaluate.return_value = "token_abc123"
        result = handler.esperar_y_resolver(page)
        assert result is True
        page.evaluate.assert_called_once()


class TestAltchaHandlerReintentos:
    def test_fallo_callback_luego_exito(self, handler, page):
        page.wait_for_selector.return_value = MagicMock()
        page.evaluate.side_effect = [None, None, "token_abc"]
        result = handler.esperar_y_resolver(page)
        assert result is True
        assert page.evaluate.call_count == 3


class TestAltchaHandlerFallbackManual:
    def test_fallback_a_manual(self, page):
        handler = AltchaHandler(max_intentos=1, pausa_manual_sec=5)
        page.wait_for_selector.return_value = MagicMock()
        page.evaluate.return_value = None
        page.wait_for_function.return_value = True
        result = handler.esperar_y_resolver(page)
        assert result is True
        page.wait_for_function.assert_called_once()

    def test_manual_timeout_falla(self, page):
        handler = AltchaHandler(max_intentos=1, pausa_manual_sec=1)
        page.wait_for_selector.return_value = MagicMock()
        page.evaluate.return_value = None
        page.wait_for_function.side_effect = Exception("timeout")
        result = handler.esperar_y_resolver(page)
        assert result is False
