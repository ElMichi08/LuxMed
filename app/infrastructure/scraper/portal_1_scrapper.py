import json
import base64
import datetime
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from pypdf import PdfReader


# ══════════════════════════════════════════════
# 0. EXCEPCIONES
# ══════════════════════════════════════════════
class ScraperError(Exception):
    pass

class PageLoadTimeoutError(ScraperError):
    pass

class LocatorNotFoundError(ScraperError):
    pass

class ButtonNotEnabledError(ScraperError):
    pass

class RSCDataNotFoundError(ScraperError):
    pass


# ══════════════════════════════════════════════
# 1. CONFIGURACIÓN (solo para test manual)
# ══════════════════════════════════════════════
URL = "https://coberturasalud.msp.gob.ec/"
CEDULA = "1401349020"
FECHA = "07-04-2026"


def _extract_blob_pdf_bytes(blob_page) -> bytes | None:
    try:
        blob_page.wait_for_load_state("networkidle", timeout=300000)
        b64 = blob_page.evaluate("""async () => {
            const resp = await fetch(location.href);
            const buf = await resp.arrayBuffer();
            const arr = new Uint8Array(buf);
            let s = '';
            for (let i = 0; i < arr.length; i++) s += String.fromCharCode(arr[i]);
            return btoa(s);
        }""")
        return base64.b64decode(b64) if b64 else None
    except Exception:
        return None


def _extract_pdf_from_iframe(page) -> bytes | None:
    try:
        iframes = page.frames
        for frame in iframes:
            url = frame.url
            if url.startswith("data:application/pdf"):
                try:
                    b64_data = url.split(",", 1)[1]
                    return base64.b64decode(b64_data)
                except Exception:
                    pass
            if url.startswith("blob:"):
                try:
                    return _extract_blob_pdf_bytes(frame)
                except Exception:
                    pass
            try:
                embed = frame.locator("embed[type='application/pdf'], object[data*='application/pdf']").first
                if embed.count() > 0:
                    data_url = embed.get_attribute("src") or embed.get_attribute("data") or ""
                    if data_url.startswith("data:application/pdf"):
                        b64_data = data_url.split(",", 1)[1]
                        return base64.b64decode(b64_data)
            except Exception:
                pass
    except Exception:
        pass
    return None


def _extract_pdf_from_page_dom(page) -> bytes | None:
    try:
        chrome_embeds = page.locator("embed[type*='pdf'], embed[original-url*='blob:']")
        embed_count = chrome_embeds.count()
        if embed_count > 0:
            print(f"[DEBUG] Encontrados {embed_count} embeds de PDF en DOM")
        
        for i in range(embed_count):
            original_url = chrome_embeds.nth(i).get_attribute("original-url") or ""
            src = chrome_embeds.nth(i).get_attribute("src") or ""
            print(f"[DEBUG] Embed #{i} — src: {src[:100]}, original-url: {original_url[:100]}")
            
            if original_url.startswith("blob:"):
                print(f"[DEBUG] Extrayendo PDF desde original-url: {original_url}")
                
                try:
                    b64 = page.evaluate(f"""async () => {{
                        try {{
                            const resp = await fetch('{original_url}');
                            if (!resp.ok) return null;
                            const buf = await resp.arrayBuffer();
                            const arr = new Uint8Array(buf);
                            let s = '';
                            for (let i = 0; i < arr.length; i++) s += String.fromCharCode(arr[i]);
                            return btoa(s);
                        }} catch(e) {{
                            return null;
                        }}
                    }}""")
                    if b64:
                        pdf_bytes = base64.b64decode(b64)
                        if _es_pdf_valido(pdf_bytes):
                            print(f"[DEBUG] *** PDF EXTRAIDO (fetch JS): {len(pdf_bytes)} bytes ***")
                            return pdf_bytes
                        else:
                            print(f"[DEBUG] Bytes extraidos pero no son PDF válido ({len(pdf_bytes)} bytes)")
                except Exception as e:
                    print(f"[DEBUG] Error en fetch JS: {e}")
                
                try:
                    temp_page = page.context.new_page()
                    temp_page.goto(original_url, wait_until="commit", timeout=10000)
                    temp_page.wait_for_load_state("networkidle", timeout=30000)
                    blob_pdf = _extract_blob_pdf_bytes(temp_page)
                    temp_page.close()
                    if blob_pdf and _es_pdf_valido(blob_pdf):
                        print(f"[DEBUG] *** PDF EXTRAIDO (temp page): {len(blob_pdf)} bytes ***")
                        return blob_pdf
                except Exception as e:
                    print(f"[DEBUG] Error en temp page: {e}")

            if src.startswith("data:application/pdf"):
                b64_data = src.split(",", 1)[1]
                pdf_bytes = base64.b64decode(b64_data)
                if _es_pdf_valido(pdf_bytes):
                    return pdf_bytes

        elements = page.locator("embed[src*='data:application/pdf'], object[data*='data:application/pdf']")
        for i in range(elements.count()):
            data_url = elements.nth(i).get_attribute("src") or elements.nth(i).get_attribute("data") or ""
            if data_url.startswith("data:application/pdf"):
                b64_data = data_url.split(",", 1)[1]
                return base64.b64decode(b64_data)

        iframe_elements = page.locator("iframe[src*='data:application/pdf']")
        for i in range(iframe_elements.count()):
            data_url = iframe_elements.nth(i).get_attribute("src") or ""
            if data_url.startswith("data:application/pdf"):
                b64_data = data_url.split(",", 1)[1]
                return base64.b64decode(b64_data)

        pdf_links = page.locator("a[href*='.pdf'], a[href*='application/pdf']")
        for i in range(pdf_links.count()):
            href = pdf_links.nth(i).get_attribute("href") or ""
            if href.startswith("data:application/pdf"):
                b64_data = href.split(",", 1)[1]
                return base64.b64decode(b64_data)
    except Exception:
        pass
    return None


def _es_pdf_valido(data: bytes) -> bool:
    if not data or len(data) < 100:
        return False
    return data[:5] == b'%PDF-'


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
def wait_for_page_ready(page, locator_str: str, timeout_sec: int = 300) -> None:
    try:
        page.locator(locator_str).wait_for(state="visible", timeout=timeout_sec * 1000)
    except PlaywrightTimeoutError as e:
        raise PageLoadTimeoutError(
            f"Timeout ({timeout_sec}s) esperando locator: {locator_str}"
        ) from e


def wait_for_button_enabled(page, locator_str: str, timeout_sec: int = 180) -> None:
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
def scrape_cobertura(url: str, cedula: str, fecha: str, headless: bool = True) -> tuple[str, bytes | None]:
    rsc_responses = []
    datos_consulta_rsc = None
    blob_pdf_texto = None
    blob_pdf_bytes = None
    blob_page_capturada = [None]

    with sync_playwright() as pw:
        args = ["--disable-blink-features=AutomationControlled"]
        if not headless:
            args.append("--window-position=-5000,-5000")
        browser = pw.chromium.launch(
            headless=headless,
            slow_mo=0 if headless else 50,
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

        page.goto(url, wait_until="networkidle")
        wait_for_page_ready(page, "input#cedula", timeout_sec=300)
        page.wait_for_timeout(3000)

        page.locator("input#cedula").fill(cedula)

        page.wait_for_timeout(2000)
        
        fecha_selectors = [
            "input:not(#cedula):not([type='hidden'])",  # cualquier input que no sea cédula ni hidden
            "input[type='text']:nth-of-type(2)",        # segundo input text
            "input[name*='fecha']",                      # input con 'fecha' en el nombre
            "input[placeholder*='fecha']",               # input con 'fecha' en placeholder
        ]
        
        campo_fecha = None
        for selector in fecha_selectors:
            candidates = page.locator(selector)
            count = candidates.count()
            if count > 0:
                for i in range(count):
                    candidate = candidates.nth(i)
                    candidate_id = candidate.get_attribute("id") or ""
                    if "cedula" not in candidate_id.lower():
                        campo_fecha = candidate
                        print(f"[DEBUG] Campo fecha encontrado con selector '{selector}' (id: {candidate_id})")
                        break
            if campo_fecha is not None:
                break
        
        if campo_fecha is None:
            todos_inputs = page.locator("input:not([type='hidden'])")
            count = todos_inputs.count()
            print(f"[DEBUG] Inputs visibles en página: {count}")
            if count < 2:
                for i in range(count):
                    inp = todos_inputs.nth(i)
                    print(f"[DEBUG]   Input #{i}: id={inp.get_attribute('id')}, type={inp.get_attribute('type')}, name={inp.get_attribute('name')}")
                raise LocatorNotFoundError("No se encontró el campo de fecha (se esperaban ≥2 inputs visibles)")
            campo_fecha = todos_inputs.nth(1)
        
        campo_fecha.fill(fecha)

        wait_for_button_enabled(page, "button:has-text('Consultar')", timeout_sec=180)
        boton_consultar = page.locator("button").filter(has_text="Consultar")

        def on_response(response):
            ct = response.headers.get("content-type", "")
            url = response.url
            if "text/x-component" in ct:
                try:
                    raw = response.body()
                    body = raw.decode("utf-8")
                    rsc_responses.append(body)
                except Exception:
                    pass
            if "application/pdf" in ct or url.lower().endswith(".pdf"):
                try:
                    pdf_bytes = response.body()
                    if _es_pdf_valido(pdf_bytes):
                        nonlocal blob_pdf_bytes
                        blob_pdf_bytes = pdf_bytes
                        print(f"[DEBUG] *** PDF capturado de RED: {len(pdf_bytes)} bytes a los {time.time() - tiempo_inicio:.1f}s ***")
                except Exception:
                    pass

        page.on("response", on_response)

        def on_new_page(nueva_pagina):
            print(f"[DEBUG] Nueva pagina detectada: {nueva_pagina.url[:80]}")
            if nueva_pagina.url.startswith("blob:"):
                blob_page_capturada[0] = nueva_pagina
                print("[DEBUG] Blob page capturada!")

        context.on("page", on_new_page)

        downloads_capturados = []
        def on_download(download):
            print(f"[DEBUG] Descarga detectada: {download.suggested_filename}")
            downloads_capturados.append(download)

        context.on("download", on_download)

        print(f"[DEBUG] Haciendo click en Consultar...")
        boton_consultar.click()
        print(f"[DEBUG] Click realizado, entrando en loop de 5 minutos...")

        tiempo_inicio = time.time()
        tiempo_maximo = 5 * 60  # 5 minutos
        rsc_found = False
        
        while True:
            elapsed = time.time() - tiempo_inicio
            
            if not rsc_found:
                for rsc_body in rsc_responses:
                    if "coberturaSalud" in rsc_body:
                        rsc_found = True
                        print(f"[DEBUG] RSC data encontrada a los {elapsed:.1f}s")
                        break
            
            # ── ESTRATEGIA 1: Blob page capturada ──
            if blob_page_capturada[0] is not None and blob_pdf_bytes is None:
                bp = blob_page_capturada[0]
                try:
                    bp.wait_for_load_state("networkidle", timeout=5000)
                    blob_pdf_texto = bp.inner_text("body")
                    blob_pdf_bytes = _extract_blob_pdf_bytes(bp)
                    if blob_pdf_bytes and _es_pdf_valido(blob_pdf_bytes):
                        print(f"[DEBUG] *** PDF EXTRAIDO (blob page): {len(blob_pdf_bytes)} bytes a los {elapsed:.1f}s ***")
                except Exception as e:
                    pass
            
            # ── ESTRATEGIA 2: Buscar en TODAS las pages del context ──
            if blob_pdf_bytes is None:
                for p in context.pages:
                    if p.url.startswith("blob:"):
                        try:
                            p.wait_for_load_state("networkidle", timeout=5000)
                            blob_pdf_texto = p.inner_text("body")
                            blob_pdf_bytes = _extract_blob_pdf_bytes(p)
                            if blob_pdf_bytes and _es_pdf_valido(blob_pdf_bytes):
                                print(f"[DEBUG] *** PDF EXTRAIDO (context.pages): {len(blob_pdf_bytes)} bytes a los {elapsed:.1f}s ***")
                                break
                        except Exception:
                            pass
            
            # ── ESTRATEGIA 3: Buscar en iframes ──
            if blob_pdf_bytes is None:
                blob_pdf_bytes = _extract_pdf_from_iframe(page)
                if blob_pdf_bytes and _es_pdf_valido(blob_pdf_bytes):
                    print(f"[DEBUG] *** PDF EXTRAIDO (iframe): {len(blob_pdf_bytes)} bytes a los {elapsed:.1f}s ***")
            
            # ── ESTRATEGIA 4: Buscar en DOM (embed/object/data URLs) ──
            if blob_pdf_bytes is None:
                blob_pdf_bytes = _extract_pdf_from_page_dom(page)
                if blob_pdf_bytes and _es_pdf_valido(blob_pdf_bytes):
                    print(f"[DEBUG] *** PDF EXTRAIDO (DOM): {len(blob_pdf_bytes)} bytes a los {elapsed:.1f}s ***")
                elif elapsed > 5 and int(elapsed) % 30 == 0:
                    embed_count = page.locator("embed").count()
                    iframe_count = page.locator("iframe").count()
                    print(f"[DEBUG] DOM check a los {elapsed:.0f}s — embeds: {embed_count}, iframes: {iframe_count}")
            
            # ── ESTRATEGIA 5: Procesar descargas ──
            if blob_pdf_bytes is None and downloads_capturados:
                for download in downloads_capturados:
                    try:
                        path = download.path()
                        if path:
                            blob_pdf_bytes = Path(path).read_bytes()
                            if blob_pdf_bytes and _es_pdf_valido(blob_pdf_bytes):
                                print(f"[DEBUG] *** PDF EXTRAIDO (download): {len(blob_pdf_bytes)} bytes a los {elapsed:.1f}s ***")
                                break
                    except Exception:
                        pass
            
            if int(elapsed) % 10 == 0 and elapsed > 0:
                pdf_status = "SI" if blob_pdf_bytes else "NO"
                rsc_status = "SI" if rsc_found else "NO"
                pages_count = len(context.pages)
                blob_pages = sum(1 for p in context.pages if p.url.startswith("blob:"))
                print(f"[DEBUG] {elapsed:.0f}s / {tiempo_maximo}s - RSC: {rsc_status} - PDF: {pdf_status} - Pages: {pages_count} - BlobPages: {blob_pages}")
            
            if blob_pdf_bytes is not None and rsc_found:
                print(f"[DEBUG] PDF y RSC obtenidos, saliendo a los {elapsed:.1f}s")
                break
            
            if blob_pdf_bytes is not None and not rsc_found and elapsed > 30:
                print(f"[DEBUG] PDF obtenido sin RSC, saliendo a los {elapsed:.1f}s (sin datos RSC)")
                break
            
            if elapsed >= tiempo_maximo:
                print(f"[DEBUG] Tiempo maximo de 5 minutos alcanzado")
                break
            
            page.wait_for_timeout(2000)

        for rsc_body in rsc_responses:
            if "coberturaSalud" in rsc_body:
                datos = extraer_datos_rsc(rsc_body)
                if datos:
                    datos_consulta_rsc = fix_datos_encoding(datos)
                    break

        if datos_consulta_rsc is None:
            if blob_pdf_bytes is not None:
                print("[DEBUG] RSC no encontrado pero PDF disponible — continuando con PDF solamente")
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
                lineas.append("NOTA: Datos RSC no disponibles — solo PDF capturado")
                lineas.append("")
                print(f"[DEBUG] Cerrando browser...")
                browser.close()
                print(f"[DEBUG] Browser cerrado. PDF: Si ({len(blob_pdf_bytes)} bytes)")
                return "\n".join(lineas), blob_pdf_bytes
            raise RSCDataNotFoundError("No se encontraron datos de cobertura en respuestas RSC")

        resultados = formatear_resultados(datos_consulta_rsc)

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

        print(f"[DEBUG] Cerrando browser...")
        browser.close()
        print(f"[DEBUG] Browser cerrado. PDF: {'Si' if blob_pdf_bytes else 'No'} ({len(blob_pdf_bytes) if blob_pdf_bytes else 0} bytes)")
        return "\n".join(lineas), blob_pdf_bytes


if __name__ == "__main__":
    try:
        resultado_texto, resultado_pdf = scrape_cobertura(URL, CEDULA, FECHA, headless=False)
        print(resultado_texto)
        if resultado_pdf:
            print(f"\n[PDF capturado: {len(resultado_pdf)} bytes]")
    except ScraperError as e:
        print(f"[ERROR] {e}")
        exit(1)