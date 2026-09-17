from unittest.mock import MagicMock, patch, PropertyMock
import pytest
from datetime import date
from app.infrastructure.scraper.portal3_adapter import Portal3Adapter
from app.infrastructure.scraper.cookie_store import CookieStore
from app.infrastructure.scraper.session_validator import SessionValidator
from app.domain.entities import Paciente


def _make_paciente():
    return Paciente(
        nombre_y_apellidos="TEST PACIENTE",
        cedula="0105556567",
        fecha_nacimiento=date(1990, 1, 1),
        aporta="ISSFA",
        fecha_atencion=date.today(),
        nom_establecimiento="HOSPITAL TEST",
    )


@pytest.fixture
def store(tmp_path):
    return CookieStore(path=tmp_path / "test_cookies.json")


@pytest.fixture
def adapter(store):
    return Portal3Adapter(cookie_store=store, headless=True)


class TestExisteAutenticacion:
    def test_no_cookies_returns_false(self, adapter):
        assert adapter.existe_autenticacion_portal_3() is False

    def test_with_valid_session(self, store, adapter):
        store.save([{"name": "sid", "value": "abc", "domain": ".msp.gob.ec", "path": "/"}])
        with patch.object(adapter._validator, "is_valid", return_value=True):
            assert adapter.existe_autenticacion_portal_3() is True


class TestProcesarPortal3:
    def test_no_cookies_returns_none(self, adapter):
        paciente = _make_paciente()
        result = adapter.procesar_portal_3(paciente)
        assert result is None

    def test_returns_none_when_no_pdf_modal(self, store):
        pytest.skip("Internal flow requires full Playwright mock — covered by integration test")
