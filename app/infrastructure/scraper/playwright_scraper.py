from __future__ import annotations
import os
import json
from datetime import date
from playwright.sync_api import sync_playwright
from app.domain.entities import Paciente
from app.domain.ports import IScraperService

class PlaywrightScraper(IScraperService):
    def __init__(self, ruta_auth: str = "data/auth_portal3.json", headless: bool = True) -> None:
        self._ruta_auth = ruta_auth
        self._headless = headless
        self._url_p1 = "https://coberturasalud.msp.gob.ec/"
        self._url_p2 = "https://app.iess.gob.ec/gestion-calificacion-derecho-web/public/formulariosContacto.jsf"
        self._url_p3 = "https://sgrdacaa.msp.gob.ec/"

    def existe_autenticacion_portal_3(self) -> bool:
        return os.path.exists(self._ruta_auth)

    def vincular_sesion_portal_3(self) -> bool:
        os.makedirs(os.path.dirname(self._ruta_auth), exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            page.goto(self._url_p3)
            try:
                page.wait_for_url("**/dashboard", timeout=120000)
                context.storage_state(path=self._ruta_auth)
                return True
            except Exception:
                return False
            finally:
                browser.close()

    def procesar_portal_1(self, cedula: str, fecha_atencion: date) -> tuple[str, str, str, bytes | None]:
        rsc_responses = []
        fecha_str = fecha_atencion.strftime("%d-%m-%Y")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self._headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                locale="es-EC",
                timezone_id="America/Guayaquil"
            )
            page = context.new_page()
            
            def on_response(response):
                ct = response.headers.get("content-type", "")
                if "text/x-component" in ct:
                    try:
                        rsc_responses.append(response.body().decode("utf-8"))
                    except Exception:
                        pass

            page.on("response", on_response)
            page.goto(self._url_p1, wait_until="networkidle")
            page.locator("input#cedula").fill(cedula)
            
            todos_inputs = page.locator("input")
            if todos_inputs.count() >= 2:
                todos_inputs.nth(1).fill(fecha_str)
                
            page.locator("button:has-text('Consultar')").wait_for(state="visible", timeout=10000)
            page.locator("button:has-text('Consultar')").click()
            
            pdf_bytes = None
            with context.expect_page(timeout=10000) as new_page_info:
                pass
            if new_page_info.value:
                pdf_bytes = new_page_info.value.pdf()

            entidad = "NINGUNA"
            tipo_seguro = "no registra cobertura"
            registro_cobertura = "no registra cobertura"
            
            for rsc in rsc_responses:
                if "coberturaSalud" in rsc:
                    for linea in rsc.split("\n"):
                        if linea.strip().startswith("1:"):
                            try:
                                data = json.loads(linea.strip()[2:])
                                if data.get("success") == "success":
                                    aseguradoras = data["data"]["coberturaSalud"]["CoberturaSeguros"]["aseguradora"]
                                    for asp in aseguradoras:
                                        reg_cob = str(asp.get("EstadoCobertura", "")).strip()
                                        if "no registra" not in reg_cob.lower():
                                            entidad = str(asp.get("NombreInstitucion", "")).strip()
                                            tipo_seguro = str(asp.get("TipoSeguro", "")).strip()
                                            registro_cobertura = reg_cob
                                            break
                            except Exception:
                                continue
            
            return (entidad, tipo_seguro, registro_cobertura, pdf_bytes)

    def extraer_acreditador_portal_2(self, paciente: Paciente) -> str | None:
        fecha_str = paciente.fecha_atencion.strftime("%d/%m/%Y")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self._headless,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context()
            page = context.new_page()
            page.goto(self._url_p2)
            
            page.locator('input[name="identificacion"]').fill(paciente.cedula)
            page.evaluate(f"document.getElementById('formConsulta:fecha_input').value = '{fecha_str}'")
            page.locator("#formConsulta\:contingencia_select_label").click()
            page.locator("li:has-text('Enfermedad')").click()
            
            try:
                page.wait_for_selector('altcha-widget[state="verified"]', timeout=30000)
            except Exception:
                pass
                
            page.locator('button:has-text("Aceptar")').click()
            page.wait_for_load_state("networkidle")
            
            tabla_azul = page.query_selector("#formConsulta\:table")
            cedula_acreditador = None
            if tabla_azul:
                celda_ci = tabla_azul.locator("td").nth(1)
                if celda_ci.count() > 0:
                    cedula_acreditador = celda_ci.text_content().strip()
                    
            return cedula_acreditador
