from __future__ import annotations
import logging
import re
from datetime import date
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError
from app.domain.entities import Paciente
from app.infrastructure.scraper.altcha_handler import AltchaHandler

logger = logging.getLogger(__name__)

PORTAL_2_URL = (
    "https://app.iess.gob.ec/gestion-calificacion-derecho-web/"
    "public/formulariosContacto.jsf"
)
CEDULA_INPUT = "#formConsulta\\:cedula_text"
FECHA_INPUT = "#formConsulta\\:fec_calendar_input"
CONTINGENCIA_LABEL = "#formConsulta\\:contingencia_select_label"
TABLA_CREDITADOR_ID = "formConsulta:table"
TABLE_DATA_ID = "formConsulta:table_data"
GRIDCELL_SELECTOR = f"#{TABLE_DATA_ID} td[role='gridcell']"
CEDULA_REGEX = re.compile(r"^\d{10}$")


class MenorSinAcreditador(Exception):
    pass


class ExtractionError(Exception):
    pass


class Portal2IessAdapter:
    def __init__(
        self,
        altcha_handler: AltchaHandler | None = None,
        headless: bool = True,
    ) -> None:
        self._altcha = altcha_handler or AltchaHandler()
        self._headless = headless

    def extraer_acreditador(
        self, cedula: str, fecha_atencion: date, paciente: Paciente
    ) -> str | None:
        fecha_str = fecha_atencion.strftime("%d-%m-%Y")
        print(f"[DEBUG Portal2] extraer_acreditador called for cedula: {cedula}")
        with sync_playwright() as pw:
            args = ["--disable-blink-features=AutomationControlled"]
            if not self._headless:
                args.append("--window-position=-5000,-5000")
            browser = pw.chromium.launch(
                headless=self._headless,
                args=args,
            )
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                locale="es-EC",
                timezone_id="America/Guayaquil",
            )
            page = context.new_page()
            try:
                return self._flujo_completo(page, cedula, fecha_str, paciente)
            finally:
                browser.close()

    def _flujo_completo(
        self, page: Page, cedula: str, fecha_str: str, paciente: Paciente
    ) -> str | None:
        print(f"[DEBUG Portal2] Navegando a: {PORTAL_2_URL}")
        page.goto(PORTAL_2_URL, wait_until="domcontentloaded", timeout=300000)
        
        page.wait_for_load_state("networkidle", timeout=30000)
        page.wait_for_timeout(1000)
        
        if page.url == "about:blank" or not page.title():
            print(f"[DEBUG Portal2] WARN: Pagina sigue en about:blank, reintentando goto...")
            page.goto(PORTAL_2_URL, wait_until="networkidle", timeout=300000)
            page.wait_for_timeout(2000)
        
        print(f"[DEBUG Portal2] URL final: {page.url}")
        print(f"[DEBUG Portal2] Titulo final: {page.title()}")
        
        self._llenar_formulario(page, cedula, fecha_str)
        
        print(f"[DEBUG Portal2] Verificando ALTCHA...")
        altcha_widget = page.locator("altcha-widget, [class*='altcha'], #altcha")
        print(f"[DEBUG Portal2] Widgets ALTCHA encontrados: {altcha_widget.count()}")
        resuelto = self._altcha.esperar_y_resolver(page)
        print(f"[DEBUG Portal2] ALTCHA resuelto: {resuelto}")
        if not resuelto:
            logger.error("ALTCHA no resuelto — abortando Portal 2")
            return None
        
        print(f"[DEBUG Portal2] ALTCHA resuelto, buscando tabla de resultados...")
        page.wait_for_timeout(1000)
        
        return self._detectar_y_extraer(page, paciente)

    def _llenar_formulario(self, page: Page, cedula: str, fecha_str: str) -> None:
        print(f"[DEBUG Portal2] Esperando input cedula: {CEDULA_INPUT}")
        page.wait_for_selector(CEDULA_INPUT, timeout=300000)
        print(f"[DEBUG Portal2] Llenando cedula: {cedula}")
        page.locator(CEDULA_INPUT).fill(cedula)
        
        print(f"[DEBUG Portal2] Llenando fecha via JS: {fecha_str}")
        
        page.evaluate("""(fecha) => {
            const input = document.getElementById('formConsulta:fec_calendar_input');
            if (!input) return;
            
            // Método 1: PrimeFaces widget
            try {
                const widget = PrimeFaces.widgets['formConsulta\\:fec_calendar'];
                if (widget && widget.setDate) {
                    // PrimeFaces espera formato DD/MM/YYYY o MM/DD/YYYY según locale
                    // Convertir de DD-MM-YYYY a DD/MM/YYYY
                    const parts = fecha.split('-');
                    const formatted = parts[0] + '/' + parts[1] + '/' + parts[2];
                    widget.setDate(new Date(parseInt(parts[2]), parseInt(parts[1])-1, parseInt(parts[0])));
                    return;
                }
            } catch(e) {}
            
            // Método 2: jQuery datepicker setDate
            try {
                const $input = jQuery(input);
                const parts = fecha.split('-');
                const d = new Date(parseInt(parts[2]), parseInt(parts[1])-1, parseInt(parts[0]));
                $input.datepicker('setDate', d);
                $input.trigger('change');
                return;
            } catch(e) {}
            
            // Método 3: Forzar valor directo + eventos
            input.removeAttribute('readonly');
            input.readOnly = false;
            input.value = fecha;
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            input.dispatchEvent(new Event('blur', { bubbles: true }));
            input.readOnly = true;
            input.setAttribute('readonly', 'readonly');
        }""", fecha_str)
        
        try:
            print(f"[DEBUG Portal2] Seleccionando contingencia...")
            page.locator(CONTINGENCIA_LABEL).click()
            page.wait_for_timeout(500)
            
            opciones = page.locator("li.ui-selectonemenu-item, ul.ui-selectonemenu-items li")
            print(f"[DEBUG Portal2] Opciones de contingencia encontradas: {opciones.count()}")
            
            clicked = False
            for i in range(opciones.count()):
                texto = opciones.nth(i).inner_text().strip()
                print(f"[DEBUG Portal2]   Opcion #{i}: '{texto}'")
                if "enfermedad" in texto.lower():
                    opciones.nth(i).click()
                    clicked = True
                    print(f"[DEBUG Portal2] Contingencia '{texto}' seleccionada")
                    break
            
            if not clicked:
                fallback = page.locator("li:has-text('Enfermedad')")
                if fallback.count() > 0:
                    fallback.first.click()
                    clicked = True
                    print(f"[DEBUG Portal2] Contingencia seleccionada via fallback")
            
            if not clicked:
                print(f"[DEBUG Portal2] WARN: No se pudo seleccionar contingencia")
            
            page.wait_for_timeout(500)
            
            aceptar = page.locator("button:has-text('Aceptar'), button:has-text('Apply'), .ui-growl-accept")
            if aceptar.count() > 0:
                aceptar.first.click()
                print(f"[DEBUG Portal2] Botón Aceptar clickeado")
                page.wait_for_timeout(1000)  # Wait for form submission
                
        except PlaywrightTimeoutError:
            logger.warning("No se pudo seleccionar contingencia — usando valor por defecto")

    def _detectar_y_extraer(
        self, page: Page, paciente: Paciente
    ) -> str | None:
        print(f"[DEBUG Portal2] Buscando tabla de acreditador...")
        
        from app.infrastructure.scraper.retry_utils import retry_with_backoff
        
        def _check_table():
            try:
                page.wait_for_load_state("domcontentloaded", timeout=5000)
            except PlaywrightTimeoutError:
                pass
            page.wait_for_timeout(500) 
            
            existe = page.evaluate("""() => {
                const el = document.getElementById('formConsulta:table_data');
                if (!el) return false;
                const rows = el.querySelectorAll('tr');
                return rows.length > 0;
            }""")
            if not existe:
                raise PlaywrightTimeoutError("Tabla no encontrada")
            return True
        
        try:
            retry_with_backoff(
                _check_table,
                max_retries=3,
                base_delay=3.0,
                max_delay=10.0,
                description="tabla acreditador Portal 2",
            )
            print(f"[DEBUG Portal2] Tabla con datos encontrada!")
        except PlaywrightTimeoutError:
            print(f"[DEBUG Portal2] Tabla no apareció tras reintentos")
            return self._sin_tabla(paciente)
        
        cedula_acreditador = self._extraer_celda_gridcell(page)
        if cedula_acreditador:
            print(f"[DEBUG Portal2] Acreditador encontrado: {cedula_acreditador}")
        else:
            print(f"[DEBUG Portal2] No se encontro cedula de acreditador en tabla")
        return cedula_acreditador

    def _sin_tabla(self, paciente: Paciente) -> str | None:
        if paciente.es_menor_de_edad:
            print(f"[DEBUG Portal2] Paciente {paciente.cedula} es menor de edad ({paciente.edad} años) — sin tabla de acreditador")
            return None
        print(f"[DEBUG Portal2] Paciente {paciente.cedula} sin tabla — afiliado directo (edad {paciente.edad})")
        return None

    def _extraer_celda_gridcell(self, page: Page) -> str | None:
        celdas_data = page.evaluate("""() => {
            const tbody = document.getElementById('formConsulta:table_data');
            if (!tbody) return [];
            const cells = tbody.querySelectorAll('td[role="gridcell"]');
            return Array.from(cells).map(td => td.innerText.trim());
        }""")
        
        print(f"[DEBUG Portal2] Celdas gridcell encontradas: {len(celdas_data)}")
        for i, texto in enumerate(celdas_data):
            print(f"[DEBUG Portal2]   Celda #{i}: '{texto}'")
            if CEDULA_REGEX.match(texto):
                return texto
        
        all_cells = page.evaluate("""() => {
            const cells = document.querySelectorAll('td[role="gridcell"]');
            return Array.from(cells).map(td => td.innerText.trim());
        }""")
        print(f"[DEBUG Portal2] Todas las celdas gridcell: {len(all_cells)}")
        for i, texto in enumerate(all_cells):
            if CEDULA_REGEX.match(texto):
                print(f"[DEBUG Portal2]   Cedula encontrada en td #{i}: '{texto}'")
                return texto
        
        print(f"[DEBUG Portal2] Ninguna celda contiene cedula valida (10 digitos)")
        return None