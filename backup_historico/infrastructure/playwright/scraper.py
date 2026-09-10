import json
import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from pypdf import PdfReader


# ══════════════════════════════════════════════
# EXCEPCIONES PERSONALIZADAS
# ══════════════════════════════════════════════
class ScraperError(Exception):
    """Base para errores del scraper."""
    pass


class PageLoadTimeoutError(ScraperError):
    """La página no cargó en el tiempo esperado."""
    pass


class LocatorNotFoundError(ScraperError):
    """Un locator no apareció en el DOM."""
    pass


class ButtonNotEnabledError(ScraperError):
    """El botón no se habilitó tras llenar los campos."""
    pass


class RSCDataNotFoundError(ScraperError):
    """No se encontraron datos de cobertura en respuestas RSC."""
    pass


class PDFNotFoundError(ScraperError):
    """No se pudo capturar el PDF (blob)."""
    pass


# ══════════════════════════════════════════════
# 1. CONFIGURACIÓN (solo para test manual)
# ══════════════════════════════════════════════
URL = "https://coberturasalud.msp.gob.ec/"
CEDULA = "1401349020"
FECHA = "07-04-2026"          # placeholder del sitio: DD-MM-YYYY


# ══════════════════════════════════════════════
# 2. FUNCIONES DE EQUIPO (SIN CAMBIOS)
# ══════════════════════════════════════════════
def fix_mojibake(text: str) -> str:
    try:
        return text.encode("latin-1", errors="replace").decode("utf-8", errors="replace")
    except Exception:
        return text


def extraer_datos_rsc(texto_rsc: str) -> dict | None:
    for linea in texto_rsc.split("\n"):
        linea = linea.strip()
        if linea.startswith("1:"):
            json_str = linea[2:]
            try:
                data = json.loads(json_str)
                if data.get("success") == "success":
                    return data["data"]
            except (json.JSONDecodeError, KeyError):
                continue
    return None


def fix_datos_encoding(data):
    if isinstance(data, dict):
        return {k: fix_datos_encoding(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [fix_datos_encoding(v) for v in data]
    elif isinstance(data, str):
        return fix_mojibake(data)
    return data


def formatear_resultados(data: dict) -> list[dict]:
    resultados = []

    aseguradoras = (
        data.get("coberturaSalud", {})
        .get("CoberturaSeguros", {})
        .get("aseguradora", [])
    )

    for asp in aseguradoras:
        resultados.append({
            "institucion": asp.get("NombreInstitucion", ""),
            "nombre": asp.get("Nombre", ""),
            "tipo_seguro": asp.get("TipoSeguro", ""),
            "estado_cobertura": asp.get("EstadoCobertura", ""),
            "mensaje": asp.get("MensajeServicioExterno", ""),
        })

    return resultados


# ══════════════════════════════════════════════
# 3. UTILIDADES DE ESPERA
# ══════════════════════════════════════════════
def wait_for_page_ready(page, locator_str: str, timeout_sec: int = 60) -> None:
    """
    Espera a que un locator sea visible (máx timeout_sec).
    Lanza PageLoadTimeoutError si expira.
    """
    try:
        page.locator(locator_str).wait_for(state="visible", timeout=timeout_sec * 1000)
    except PlaywrightTimeoutError as e:
        raise PageLoadTimeoutError(
            f"Timeout ({timeout_sec}s) esperando locator: {locator_str}"
        ) from e


def wait_for_button_enabled(page, locator_str: str, timeout_sec: int = 30) -> None:
    """
    Espera a que un botón esté habilitado (máx timeout_sec).
    Lanza ButtonNotEnabledError si expira.
    """
    boton = page.locator(locator_str)
    try:
        boton.wait_for(state="visible", timeout=timeout_sec * 1000)
    except PlaywrightTimeoutError as e:
        raise LocatorNotFoundError(
            f"Botón no apareció en {timeout_sec}s: {locator_str}"
        ) from e

    limite = datetime.datetime.now() + datetime.timedelta(seconds=timeout_sec)
    while datetime.datetime.now() < limite:
        if boton.is_enabled():
            return
        page.wait_for_timeout(500)
    raise ButtonNotEnabledError(
        f"Botón no se habilitó en {timeout_sec}s: {locator_str}"
    )


# ══════════════════════════════════════════════
# 4. FUNCIÓN PRINCIPAL REUTILIZABLE
# ══════════════════════════════════════════════
def scrape_cobertura(url: str, cedula: str, fecha: str, headless: bool = True) -> str:
    """
    Ejecuta el flujo completo de consulta de cobertura.
    Retorna el texto formateado (igual a resultado_cobertura.txt).
    Lanza excepciones ScraperError en cualquier fallo.
    """
    rsc_responses = []
    datos_consulta_rsc = None
    blob_pdf_texto = None
    blob_page_capturada = [None]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=headless,
            slow_mo=0 if headless else 50,
            args=["--disable-blink-features=AutomationControlled"],
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

        # 1. NAVEGAR + espera 60s carga inicial
        page.goto(url, wait_until="networkidle")
        wait_for_page_ready(page, "input#cedula", timeout_sec=60)

        # 2. LLENAR CÉDULA (fill directo, sin simulación humana)
        page.locator("input#cedula").fill(cedula)

        # 3. LLENAR FECHA (segundo input de la página)
        todos_inputs = page.locator("input")
        count = todos_inputs.count()
        if count < 2:
            raise LocatorNotFoundError("No se encontró el campo de fecha (se esperaban ≥2 inputs)")
        campo_fecha = todos_inputs.nth(1)
        campo_fecha.fill(fecha)

        # 4. BOTÓN CONSULTAR - esperar habilitado
        wait_for_button_enabled(page, "button:has-text('Consultar')", timeout_sec=30)
        boton_consultar = page.locator("button").filter(has_text="Consultar")

        # 5. INTERCEPTAR RESPUESTAS RSC
        def on_response(response):
            ct = response.headers.get("content-type", "")
            if "text/x-component" in ct:
                try:
                    raw = response.body()
                    body = raw.decode("utf-8")
                    rsc_responses.append(body)
                except Exception:
                    pass

        page.on("response", on_response)

        # 6. CAPTURAR PÁGINA BLOB (PDF)
        def on_new_page(nueva_pagina):
            if nueva_pagina.url.startswith("blob:"):
                blob_page_capturada[0] = nueva_pagina

        context.on("page", on_new_page)

        # 7. CLIC EN CONSULTAR
        boton_consultar.click()

        # 8. ESPERAR RESPUESTA RSC CON DATOS (máx 20s)
        for _ in range(40):
            page.wait_for_timeout(500)
            for rsc_body in rsc_responses:
                if "coberturaSalud" in rsc_body:
                    break
            else:
                continue
            break

        # 9. EXTRAER DATOS RSC
        for rsc_body in rsc_responses:
            if "coberturaSalud" in rsc_body:
                datos = extraer_datos_rsc(rsc_body)
                if datos:
                    datos_consulta_rsc = fix_datos_encoding(datos)
                    break

        if datos_consulta_rsc is None:
            raise RSCDataNotFoundError("No se encontraron datos de cobertura en respuestas RSC")

        resultados = formatear_resultados(datos_consulta_rsc)

        # 10. CAPTURAR PDF BLOB (espera hasta 10s)
        if blob_page_capturada[0] is not None:
            bp = blob_page_capturada[0]
            try:
                bp.wait_for_load_state("networkidle", timeout=10000)
                blob_pdf_texto = bp.inner_text("body")
            except PlaywrightTimeoutError:
                pass  # PDF opcional, continuamos con datos RSC
        else:
            for p in context.pages:
                if p.url.startswith("blob:"):
                    try:
                        p.wait_for_load_state("networkidle", timeout=5000)
                        blob_pdf_texto = p.inner_text("body")
                        break
                    except PlaywrightTimeoutError:
                        pass

        # 11. CONSTRUIR TEXTO DE SALIDA (formato idéntico al .txt actual)
        lineas = []
        lineas.append("=" * 55)
        lineas.append("  RESULTADO CONSULTA COBERTURA DE SALUD")
        lineas.append("  MSP ECUADOR")
        lineas.append("=" * 55)
        lineas.append("")
        lineas.append(f"Cedula          : {cedula}")
        lineas.append(f"Fecha de consulta: {fecha}")
        lineas.append("-" * 55)
        lineas.append("")

        for r in resultados:
            lineas.append(f"Institucion : {r['institucion']}")
            lineas.append(f"Nombre      : {r['nombre']}")
            lineas.append(f"Tipo Seguro : {r['tipo_seguro']}")
            lineas.append(f"Cobertura   : {r['estado_cobertura']}")
            if r['mensaje']:
                lineas.append(f"Mensaje     : {r['mensaje']}")
            lineas.append("-" * 55)
            lineas.append("")

        if blob_pdf_texto:
            lineas.append("\n--- TEXTO EXTRAIDO DEL PDF ---")
            lineas.append(blob_pdf_texto[:2000])
            lineas.append("\n--- FIN PDF ---")

        browser.close()
        return "\n".join(lineas)


# ══════════════════════════════════════════════
# 5. ENTRY POINT MÍNIMO (SOLO TEST MANUAL)
# ══════════════════════════════════════════════
if __name__ == "__main__":
    try:
        resultado = scrape_cobertura(URL, CEDULA, FECHA, headless=False)
        print(resultado)
    except ScraperError as e:
        print(f"[ERROR] {e}")
        exit(1)