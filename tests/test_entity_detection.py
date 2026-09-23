"""Tests for entity detection in PDF parsing — _buscar_entidad_en_lineas."""
import pytest
from app.infrastructure.scraper.playwright_scraper import _buscar_entidad_en_lineas, ENTIDADES_CONOCIDAS


class TestBuscarEntidadEnLineas:
    """Tests for the entity detection helper."""

    def test_returns_entity_on_same_line(self):
        lineas = [
            "IESS afiliado seguro general tiempo completo no cumple con el tiempo de espera requerido no registra cobertura",
            "ISSFA beneficiario montepio ok si registra cobertura",
            "ISSPOL no registra cobertura. ciudadano no encontrado",
        ]
        result = _buscar_entidad_en_lineas(lineas, 0, 3)
        assert result == "ISSFA"

    def test_returns_entity_before_match(self):
        lineas = [
            "IESS afiliado seguro general tiempo completo",
            "si registra cobertura",
            "ISSFA no registra cobertura",
        ]
        result = _buscar_entidad_en_lineas(lineas, 0, 3)
        assert result == "IESS"

    def test_returns_entity_after_match(self):
        lineas = [
            "no registra cobertura",
            "ISSFA beneficiario montepio ok si registra cobertura",
        ]
        result = _buscar_entidad_en_lineas(lineas, 0, 2)
        assert result == "ISSFA"

    def test_returns_empty_when_no_entity(self):
        lineas = [
            "some random text",
            "si registra cobertura",
            "more random text",
        ]
        result = _buscar_entidad_en_lineas(lineas, 0, 3)
        assert result == ""

    def test_handles_empty_lines(self):
        lineas = [
            "",
            "IESS afiliado",
            "",
            "si registra cobertura",
            "",
        ]
        result = _buscar_entidad_en_lineas(lineas, 0, 5)
        assert result == "IESS"

    def test_handles_out_of_bounds(self):
        lineas = ["IESS afiliado si registra cobertura"]
        result = _buscar_entidad_en_lineas(lineas, -1, 10)
        assert result == "IESS"

    def test_prefers_center_over_earlier(self):
        lineas = [
            "IESS afiliado no registra cobertura",
            "ISSFA beneficiario si registra cobertura",
        ]
        result = _buscar_entidad_en_lineas(lineas, 0, 2)
        assert result == "ISSFA"

    def test_all_known_entities(self):
        for entidad in ENTIDADES_CONOCIDAS:
            lineas = [f"{entidad} afiliado si registra cobertura"]
            result = _buscar_entidad_en_lineas(lineas, 0, 1)
            assert result == entidad, f"Failed for entity: {entidad}"
