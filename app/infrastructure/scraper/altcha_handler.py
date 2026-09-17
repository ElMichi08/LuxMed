from __future__ import annotations
import logging
from playwright.sync_api import Page

logger = logging.getLogger(__name__)

ALTCHA_WIDGET_SELECTOR = "altcha-widget"
ALTCHA_SOLVE_SCRIPT = """
async () => {
    const widget = document.querySelector('altcha-widget');
    if (!widget) return null;
    const shadow = widget.shadowRoot;
    if (!shadow) return null;
    const input = shadow.querySelector('input[name="altcha"]');
    if (input) return input.value;
    return null;
}
"""


class AltchaHandler:
    def __init__(self, pausa_manual_sec: int = 30) -> None:
        self._pausa_manual_sec = pausa_manual_sec

    def esperar_y_resolver(self, page: Page) -> bool:
        try:
            page.wait_for_selector(
                f"[class*='{ALTCHA_WIDGET_SELECTOR}'], "
                f"#{ALTCHA_WIDGET_SELECTOR}, "
                "altcha-widget",
                timeout=10000,
            )
        except Exception:
            return True

        token = page.evaluate(ALTCHA_SOLVE_SCRIPT)
        if token:
            return True

        self._traer_ventana_al_frente(page)
        return self._esperar_resolucion_manual(page)

    def _traer_ventana_al_frente(self, page: Page) -> None:
        try:
            page.evaluate("""
                () => {
                    try {
                        window.moveTo(300, 200);
                        window.resizeTo(1200, 700);
                    } catch(e) {}
                }
            """)
            try:
                page.bring_to_front()
            except Exception:
                pass
        except Exception as e:
            print(f"[DEBUG ALTCHA] No se pudo mover ventana: {e}")

    def _esperar_resolucion_manual(self, page: Page) -> bool:
        try:
            print(f"[DEBUG ALTCHA] Esperando resolución manual ({self._pausa_manual_sec}s)...")
            page.wait_for_function(
                """
                () => {
                    const widget = document.querySelector('altcha-widget');
                    if (!widget) return true;
                    const shadow = widget.shadowRoot;
                    if (!shadow) return true;
                    const input = shadow.querySelector('input[name="altcha"]');
                    return input && input.value && input.value.length > 0;
                }
                """,
                timeout=self._pausa_manual_sec * 1000,
            )
            print(f"[DEBUG ALTCHA] Resuelto manualmente!")
            return True
        except Exception:
            print(f"[DEBUG ALTCHA] Tiempo agotado — no fue resuelto")
            return False
