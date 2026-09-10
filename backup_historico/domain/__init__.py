"""Módulo de Dominio del sistema LuxMed.

Contiene las entidades, modelos y reglas de negocio puras,
sin dependencias de frameworks, librerías de scraping ni persistencia.
"""

from domain.models import AseguradoraCobertura, Portal1Result

__all__ = ["AseguradoraCobertura", "Portal1Result"]
