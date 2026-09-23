from __future__ import annotations
import logging
import os
from datetime import date
from pathlib import Path
from urllib.parse import urljoin
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, Locator, BrowserContext, TimeoutError as PlaywrightTimeoutError
from app.domain.entities import Paciente
from app.infrastructure.scraper.portal3_urls import LOGIN_URL

_env_path = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(_env_path)
PORTAL3_USUARIO = os.getenv("usuario", "")
PORTAL3_CONTRASENA = os.getenv("contraseña", "")
DEFAULT_ENTIDAD = os.getenv("DEFAULT_ENTIDAD", "27 DE OCTUBRE")
PERFIL_ENTIDAD = os.getenv("PERFIL_ENTIDAD", "DIRECCION DISTRITAL 14D01")

logger = logging.getLogger(__name__)

MODAL_SELECTOR = ".modal.show, .modal.in"


class Portal3Adapter:
    """Adapter stateless: abre y cierra browser por cada paciente."""

    def __init__(
        self,
        login_url: str = LOGIN_URL,
        headless: bool = True,
        timeout_ms: int = 300000,
    ) -> None:
        self._login_url = login_url
        self._headless = headless
        self._timeout_ms = timeout_ms

    ADAPTIVE_TIMEOUTS_MS = [30000, 45000, 60000]
    MAX_FULL_RETRIES = 1  

    def procesar_portal_3(self, paciente: Paciente) -> bytes | None:
        if not PORTAL3_USUARIO or not PORTAL3_CONTRASENA:
            logger.error("Credenciales Portal 3 no encontradas en .env")
            return None

        pdf_bytes = self._try_portal_3(paciente, retry_count=0)
        if pdf_bytes is not None:
            return pdf_bytes

        for full_retry in range(1, self.MAX_FULL_RETRIES + 1):
            logger.warning("Portal 3 retry completo %d/%d para CI=%s", 
                          full_retry, self.MAX_FULL_RETRIES, paciente.cedula)
            pdf_bytes = self._try_portal_3(paciente, retry_count=full_retry)
            if pdf_bytes is not None:
                return pdf_bytes

        logger.error("Portal 3 fallo definitivo para %s tras reintentos", paciente.cedula)
        return None

    def _try_portal_3(self, paciente: Paciente, retry_count: int) -> bytes | None:
        pw = sync_playwright().start()
        try:
            args = ["--disable-blink-features=AutomationControlled"]
            if not self._headless:
                args.append("--window-position=-5000,-5000")
            browser = pw.chromium.launch(
                headless=self._headless,
                args=args,
            )
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                locale="es-EC",
                timezone_id="America/Guayaquil",
            )
            page = context.new_page()
            page.set_default_timeout(30000)

            login_ok = False
            for timeout_ms in self.ADAPTIVE_TIMEOUTS_MS:
                try:
                    if self._login(page, context, network_timeout_ms=timeout_ms):
                        login_ok = True
                        break
                except Exception as e:
                    logger.warning("Login fallo con timeout %ds: %s", timeout_ms // 1000, e)
                    continue

            if not login_ok:
                logger.error("Login fallo tras todos los timeouts adaptativos")
                return None

            self._open_reportes_card(page)
            self._select_role_and_save(page, DEFAULT_ENTIDAD)
            self._open_historial_atenciones(page)

            entidad = paciente.nom_establecimiento or DEFAULT_ENTIDAD
            logger.info("Procesando Portal 3: CI=%s entidad=%s (intento %d)", 
                       paciente.cedula, entidad, retry_count)

            self._close_modal_if_open(page)
            self._search_patient(page, paciente, entidad)
            self._select_result_row(page, paciente)
            self._fill_motivo_and_save(page)
            pdf_bytes = self._print_atencion_and_extract_pdf(page, context, paciente)

            if pdf_bytes:
                logger.info("Portal 3 OK -- %d bytes", len(pdf_bytes))
            else:
                logger.warning("Portal 3 -- no se obtuvo PDF para CI=%s", paciente.cedula)

            return pdf_bytes

        except Exception as e:
            logger.error("Portal 3 fallo en intento %d para %s: %s", 
                        retry_count, paciente.cedula, e, exc_info=True)
            return None
        finally:
            try:
                pw.stop()
            except Exception:
                pass


    def _login(self, page: Page, context: BrowserContext, network_timeout_ms: int = 30000) -> bool:
        logger.info("Iniciando sesion Portal 3 (timeout: %ds)...", network_timeout_ms // 1000)
        page.goto(self._login_url, wait_until="domcontentloaded", timeout=network_timeout_ms)
        page.wait_for_timeout(2000)

        user_field = page.locator(
            "input[type='text'], input[name*='user'], input[name*='cedula'], "
            "input[name*='usuario'], input[id*='user'], input[id*='cedula']"
        ).first
        pass_field = page.locator("input[type='password']").first

        if user_field.count() == 0 or pass_field.count() == 0:
            logger.error("No se encontraron campos de usuario/password")
            return False

        user_field.fill(PORTAL3_USUARIO)
        page.wait_for_timeout(500)
        pass_field.fill(PORTAL3_CONTRASENA)
        page.wait_for_timeout(500)

        login_btn = page.locator(
            "button[type='submit'], button:has-text('Iniciar'), "
            "button:has-text('Entrar'), input[type='submit']"
        ).first
        if login_btn.count() > 0:
            login_btn.click()
        else:
            page.keyboard.press("Enter")

        page.wait_for_load_state("networkidle", timeout=network_timeout_ms)
        page.wait_for_timeout(1000)

        if pass_field.count() > 0 and pass_field.first.is_visible():
            logger.error("Login fallo -- campo de password aun visible")
            return False

        logger.info("Login exitoso")
        return True


    def _scroll_page(self, page: Page, pixels: int = 700) -> None:
        page.mouse.wheel(0, pixels)
        page.wait_for_timeout(100)

    def _wait_for_modal(self, page: Page, timeout_ms: int = 15000) -> Locator:
        modal = page.locator(MODAL_SELECTOR).last
        modal.wait_for(state="visible", timeout=timeout_ms)
        return modal

    def _wait_for_named_modal(self, page: Page, text: str, timeout_ms: int = 15000) -> Locator:
        modal = page.locator(MODAL_SELECTOR).filter(has_text=text).last
        try:
            modal.wait_for(state="visible", timeout=timeout_ms)
        except Exception as e:
            all_modals = page.locator(MODAL_SELECTOR).all()
            logger.error(f"[_wait_for_named_modal] Buscando modal '{text}', encontré {len(all_modals)} modales:")
            for i, m in enumerate(all_modals):
                try:
                    txt = m.inner_text(timeout=1000)[:200]
                    logger.error(f"  Modal {i}: {txt}")
                except Exception:
                    logger.error(f"  Modal {i}: (no pude leer texto)")
            raise
        return modal

    def _close_modal_if_open(self, page: Page, timeout_ms: int = 15000) -> None:
        modal = page.locator(MODAL_SELECTOR).last
        if modal.count() == 0:
            return
        try:
            if modal.is_visible():
                page.keyboard.press("Escape")
                modal.wait_for(state="hidden", timeout=timeout_ms)
        except Exception:
            pass

    def _select_entidad_chosen(self, page: Page, select_locator: Locator, target_text: str) -> None:
        container = select_locator.locator(
            "xpath=following-sibling::*[contains(@class,'chosen-container')][1]"
        )
        container.locator(".chosen-single").click()
        search_input = container.locator(".chosen-search input")
        search_input.fill(target_text)
        result = container.locator("li.active-result", has_text=target_text).first
        result.click()

    def _set_date_picker_field(self, page: Page, selector: str, value: date) -> None:
        fmt = page.evaluate(
            "(sel) => { const el = document.querySelector(sel); return el ? (el.getAttribute('data-date-format') || 'dd-mm-yyyy') : 'dd-mm-yyyy'; }",
            selector,
        )
        sep = "-" if "-" in fmt else ("/" if "/" in fmt else ".")
        date_str = f"{value.day:02d}{sep}{value.month:02d}{sep}{value.year}"

        result = page.evaluate(
            """(args) => {
                const [sel, dateStr, y, m, d] = args;
                const el = document.querySelector(sel);
                if (!el) return {error: 'element not found'};

                if (window.jQuery) {
                    try {
                        const $el = window.jQuery(el);
                        if (!$el.data('datepicker')) {
                            $el.datepicker({autoclose: true, format: 'dd-mm-yyyy', language: 'es'});
                        }
                        $el.datepicker('setDate', new Date(y, m, d));
                        $el.trigger('changeDate');
                        $el.trigger('change');
                        return {method: 'datepicker', value: el.value};
                    } catch(e) { /* fallback */ }
                }

                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeInputValueSetter.call(el, dateStr);
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
                el.dispatchEvent(new Event('blur', {bubbles: true}));
                return {method: 'direct_set', value: el.value};
            }""",
            [selector, date_str, value.year, value.month - 1, value.day],
        )
        logger.info("Datepicker %s -> %s", selector, result)


    def _open_reportes_card(self, page: Page) -> None:
        self._scroll_page(page)
        page.wait_for_timeout(500)

        modal = page.locator(MODAL_SELECTOR).last
        if modal.count() > 0 and modal.is_visible():
            logger.info("Modal ya abierto")
            return

        reportes_card = page.locator("div", has_text="Reportes").filter(
            has=page.get_by_role("button", name="Acceder")
        ).last
        if reportes_card.count() > 0 and reportes_card.is_visible():
            reportes_card.get_by_role("button", name="Acceder").click()
            self._wait_for_modal(page)
            return

        logger.warning("Tarjeta Reportes no encontrada -- usando Mis Perfiles")
        page.locator("li.dropdown-modal > a.dropdown-toggle").first.click()
        page.get_by_role("link", name="Mis Perfiles", exact=True).click()
        self._wait_for_modal(page)

    def _select_role_and_save(self, page: Page, entidad: str) -> None:
        modal = self._wait_for_modal(page)
        modal.get_by_text("Nombre", exact=True).first.click()

        perfil = os.getenv("PERFIL_ROL", "ESPECIALISTA DISTRITAL CALIDAD DE LOS SERVICIOS DE SALUD")
        perfil_entidad = os.getenv("PERFIL_ENTIDAD", "DIRECCION DISTRITAL 14D01")
        logger.info("Buscando perfil='%s' perfil_entidad='%s'", perfil, perfil_entidad)

        fila = None
        for selector in [
            f"tr:has-text('{perfil}'):has-text('{perfil_entidad}')",
            f"tr:has-text('{perfil_entidad}'):has-text('{perfil}')",
        ]:
            candidates = modal.locator(selector)
            if candidates.count() > 0:
                radio = candidates.first.locator('input[type="radio"]')
                if radio.count() > 0:
                    fila = candidates.first
                    logger.info("Fila encontrada con selector: %s", selector)
                    break

        if fila is None:
            try:
                modal_html = modal.inner_html(timeout=5000)
                logger.error(
                    "No se encontro fila. HTML de la modal (primeros 3000 chars): %s",
                    modal_html[:3000],
                )
            except Exception:
                logger.error("No se encontro fila y no se pudo leer HTML de la modal")
            raise RuntimeError(
                f"No se encontro fila con perfil='{perfil}' y entidad='{perfil_entidad}'"
            )

        fila.locator('input[type="radio"]').check(force=True)
        logger.info("Radio button seleccionado para perfil='%s'", perfil)

        self._scroll_page(page, 400)
        modal.get_by_role("button", name="Guardar").click()
        self._close_modal_if_open(page)

    def _open_historial_atenciones(self, page: Page) -> None:
        page.get_by_role("link", name="Reportes Administrativos").click()
        page.get_by_text("Historial Atenciones", exact=True).click()

        modal = self._wait_for_modal(page)
        self._scroll_page(page, 300)
        modal.get_by_role("button", name="Aceptar").click()
        self._close_modal_if_open(page)


    def _search_patient(self, page: Page, paciente: Paciente, entidad: str) -> None:

        fecha_desde = date(2026, 4, 1)
        fecha_hasta = date(2026, 4, 30)

        entidad_select = page.locator('select[name="select-entidad"]')
        self._select_entidad_chosen(page, entidad_select, entidad)
        page.wait_for_timeout(300)

        self._set_date_picker_field(page, 'input[name="paciente_fecha_desde"]', fecha_desde)
        page.wait_for_timeout(300)
        self._set_date_picker_field(page, 'input[name="paciente_fecha_hasta"]', fecha_hasta)
        page.wait_for_timeout(500)

        val_desde = page.locator('input[name="paciente_fecha_desde"]').input_value()
        val_hasta = page.locator('input[name="paciente_fecha_hasta"]').input_value()
        logger.info("Fechas seteadas: desde='%s' hasta='%s'", val_desde, val_hasta)

        ci_input = page.locator("#paciente_numeroidentificacion")
        ci_input.fill(paciente.cedula)
        page.wait_for_timeout(200)

        page.locator("#searchpacientedatatble-button").click()
        page.wait_for_timeout(1000)
        self._scroll_page(page, 500)

    def _select_result_row(self, page: Page, paciente: Paciente) -> None:
        row_cell = page.locator('td[tabindex="0"]').first
        empty_state = page.locator("td.dataTables_empty").first

        try:
            row_cell.or_(empty_state).wait_for(state="visible", timeout=10000)
        except Exception:
            logger.warning("Tabla no respondio para CI=%s", paciente.cedula)
            return

        if empty_state.is_visible():
            logger.warning("Sin resultados para CI=%s", paciente.cedula)
            return

        row_cell.click()

        child_row = row_cell.locator(
            "xpath=ancestor::tr[1]/following-sibling::tr[contains(@class,'child')][1]"
        )
        pdf_icon = child_row.locator("i.fa.fa-file-pdf-o.bigger-125.fa-fw.red").first
        pdf_icon.wait_for(state="visible", timeout=10000)
        pdf_icon.click()

    def _fill_motivo_and_save(self, page: Page) -> None:
        from app.infrastructure.scraper.retry_utils import retry_with_backoff
        modal = self._wait_for_modal(page)
        modal.locator("#impresatencionmedica_ctmotivo").select_option(value="3088")
        modal.locator("#impresatencionmedica_observacion").fill("RCPROVINCIAL")
        
        logger.debug("[_fill_motivo_and_save] Click en Guardar...")
        modal.get_by_role("button", name="Guardar").click()
        
        page.wait_for_timeout(2000)
        visible_modals = page.locator(".modal.show, .modal.in").count()
        logger.debug(f"[_fill_motivo_and_save] Modales visibles tras Guardar: {visible_modals}")
        
        error_msgs = page.locator(".alert-danger, .validation-error, .error").count()
        logger.debug(f"[_fill_motivo_and_save] Mensajes de error: {error_msgs}")
        
        retry_with_backoff(
            lambda: self._wait_for_named_modal(page, "Impresiones"),
            max_retries=3,
            base_delay=3.0,
            max_delay=10.0,
            description="modal Impresiones post-guardar",
        )

    def _print_atencion_and_extract_pdf(self, page: Page, context: BrowserContext, paciente: Paciente) -> bytes | None:
        page.locator('button[onclick="printatencionAction()"]').click()
        modal = self._wait_for_named_modal(page, "Visualizar archivo")

        viewer = modal.locator("iframe, embed, object").first
        try:
            viewer.wait_for(state="attached", timeout=15000)
        except PlaywrightTimeoutError:
            logger.warning("Visor de PDF no encontrado")
            return None

        src = viewer.get_attribute("src") or viewer.get_attribute("data") or ""
        if not src:
            return None

        if src.startswith("data:application/pdf;base64,"):
            import base64
            return base64.b64decode(src.split(",", 1)[1])

        try:
            absolute_url = urljoin(page.url, src)
            response = context.request.get(absolute_url)
            if response.ok:
                return response.body()
        except Exception as e:
            logger.error("Error descargando PDF: %s", e)
        return None