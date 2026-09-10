"""Puertos (interfaces y contratos) de la capa de aplicación."""

from application.ports.portal_gateway import (
    PortalError,
    PortalScrapingError,
    PortalTimeoutError,
    PortalUnavailableError,
    Portal1Gateway,
)

__all__ = [
    "PortalError",
    "PortalTimeoutError",
    "PortalUnavailableError",
    "PortalScrapingError",
    "Portal1Gateway",
]
