from __future__ import annotations
import logging
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from app.infrastructure.scraper.cookie_store import CookieStore
from app.infrastructure.scraper.portal3_urls import VALIDATION_URL

logger = logging.getLogger(__name__)


class SessionValidator:
    def __init__(
        self,
        cookie_store: CookieStore,
        validation_url: str = VALIDATION_URL,
        timeout_ms: int = 15000,
    ) -> None:
        self._store = cookie_store
        self._validation_url = validation_url
        self._timeout_ms = timeout_ms

    def is_valid(self) -> bool:
        cookies = self._store.load()
        if cookies is None:
            return False

        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                # Usar storage_state para restaurar cookies + localStorage/sessionStorage
                context = browser.new_context(storage_state={"cookies": cookies})
                page = context.new_page()
                try:
                    response = page.goto(
                        self._validation_url,
                        wait_until="domcontentloaded",
                        timeout=self._timeout_ms,
                    )
                    status = response.status if response else 0
                    
                    # 200 = sesión válida
                    if status == 200:
                        logger.info("Sesión válida (HTTP 200)")
                        return True
                    
                    # 401/403 = sesión expirada → borrar cookies
                    if status in (401, 403):
                        logger.warning("Sesión expirada (HTTP %d) — eliminando cookies", status)
                        self._store.delete()
                        return False
                    
                    # 302/303 = redirección probable a login → sesión expirada
                    if status in (302, 303):
                        logger.warning("Sesión expirada (redirect HTTP %d) — eliminando cookies", status)
                        self._store.delete()
                        return False
                    
                    # 404/500/otros = portal podría estar caído o URL cambió
                    # NO borrar cookies — pueden ser válidas pero la URL de validación es incorrecta
                    logger.warning("Portal devolvió HTTP %d — cookies conservadas, portal podría estar caído", status)
                    return False
                except PlaywrightTimeoutError:
                    logger.warning("Timeout validando sesión — portal podría estar caído")
                    return False
                finally:
                    context.close()
                    browser.close()
        except Exception as e:
            logger.warning("Error inesperado validando sesión: %s", e)
            return False
