from unittest.mock import MagicMock, patch, PropertyMock
import pytest
from datetime import date
from app.infrastructure.scraper.portal2_iess_adapter import (
    Portal2IessAdapter,
    MenorSinAcreditador,
    CEDULA_REGEX,
)
from app.domain.entities import Paciente, EstadoValidacion, EntidadSeguro


def _make_paciente(cedula="0105556567", edad=25):
    nac = date.today().replace(year=date.today().year - edad)
    return Paciente(
        nombre_y_apellidos="TEST PACIENTE",
        cedula=cedula,
        fecha_nacimiento=nac,
        aporta="IESS",
        fecha_atencion=date.today(),
        nom_establecimiento="HOSPITAL TEST",
    )


class TestCedulaRegex:
    def test_cedula_valida(self):
        assert CEDULA_REGEX.match("0105556567")

    def test_cedula_corta(self):
        assert not CEDULA_REGEX.match("12345")

    def test_cedula_con_letras(self):
        assert not CEDULA_REGEX.match("123456789a")

    def test_cedula_larga(self):
        assert not CEDULA_REGEX.match("01055565678")


class TestSinTabla:
    def test_adulto_sin_tabla_retorna_none(self):
        adapter = Portal2IessAdapter()
        paciente = _make_paciente(edad=25)
        result = adapter._sin_tabla(paciente)
        assert result is None

    def test_menor_sin_tabla_lanza_excepcion(self):
        adapter = Portal2IessAdapter()
        paciente = _make_paciente(edad=15)
        with pytest.raises(MenorSinAcreditador):
            adapter._sin_tabla(paciente)


class TestExtraerCedulaGridcell:
    def test_extrae_cedula_valida(self):
        adapter = Portal2IessAdapter()
        page = MagicMock()
        celda_mock = MagicMock()
        celda_mock.inner_text.return_value = "0105556567"
        locator_mock = MagicMock()
        locator_mock.count.return_value = 1
        locator_mock.nth.return_value = celda_mock
        page.locator.return_value = locator_mock
        result = adapter._extraer_celda_gridcell(page)
        assert result == "0105556567"

    def test_no_encuentra_cedula_valida(self):
        adapter = Portal2IessAdapter()
        page = MagicMock()
        celda_mock = MagicMock()
        celda_mock.inner_text.return_value = "texto invalido"
        locator_mock = MagicMock()
        locator_mock.count.return_value = 1
        locator_mock.nth.return_value = celda_mock
        page.locator.return_value = locator_mock
        result = adapter._extraer_celda_gridcell(page)
        assert result is None

    def test_celdas_vacias(self):
        adapter = Portal2IessAdapter()
        page = MagicMock()
        locator_mock = MagicMock()
        locator_mock.count.return_value = 0
        page.locator.return_value = locator_mock
        result = adapter._extraer_celda_gridcell(page)
        assert result is None


class TestExtraerAcreditador:
    @patch("app.infrastructure.scraper.portal2_iess_adapter.sync_playwright")
    def test_flujo_completo_con_tabla(self, mock_pw):
        paciente = _make_paciente()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_pw.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        mock_page.locator.return_value.wait_for.return_value = None
        celda_mock = MagicMock()
        celda_mock.inner_text.return_value = "0105556567"
        mock_page.locator.return_value.count.return_value = 1
        mock_page.locator.return_value.nth.return_value = celda_mock

        adapter = Portal2IessAdapter(headless=True)
        result = adapter.extraer_acreditador("0105556567", date.today(), paciente)
        assert result == "0105556567"

    @patch("app.infrastructure.scraper.portal2_iess_adapter.sync_playwright")
    def test_flujo_sin_tabla_adulto(self, mock_pw):
        paciente = _make_paciente(edad=25)
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_pw.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        mock_page.locator.return_value.wait_for.side_effect = PlaywrightTimeoutError("timeout")

        adapter = Portal2IessAdapter(headless=True)
        result = adapter.extraer_acreditador("0105556567", date.today(), paciente)
        assert result is None
