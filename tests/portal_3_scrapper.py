"""Automatizacion asistida del reporte "Historial de Atenciones" en LUXMED.

Uso:
    python luxmed_reportes_automation.py --generate-fake-data [--count N]
    python luxmed_reportes_automation.py --run

El login NO se scrapea: el script abre una instancia propia y aislada de
Chromium (no el navegador personal del usuario), navega a LOGIN_URL y
espera (auto-wait) a que el usuario inicie sesion manualmente hasta detectar
la tarjeta "Reportes" del home. A partir de ahi corre la automatizacion.

Selectores marcados con [EXACTO] vienen dados tal cual por el usuario.
Selectores marcados con [HEURISTICO] se infieren por texto visible porque
el sitio es una ruta protegida y no pudo inspeccionarse en vivo; revisar y
ajustar tras el primer dry-run si el sitio real no coincide.
"""

from __future__ import annotations

import argparse
import calendar
import io
import logging
import os
import random
import subprocess
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urljoin

import pdfplumber
from dotenv import load_dotenv
from openpyxl import Workbook, load_workbook
from playwright.sync_api import BrowserType, Locator, Page, sync_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("luxmed_automation")

MODAL_SELECTOR = ".modal.show, .modal.in"


@dataclass
class Settings:
    login_url: str
    headless: bool
    patients_file: Path
    output_dir: Path
    date_format: str
    login_timeout_ms: int
    navigation_timeout_ms: int
    modal_timeout_ms: int
    action_timeout_ms: int
    default_entidad: str
    perfil_entidad: str
    search_fecha_desde: str | None
    search_fecha_hasta: str | None
    step_pause_ms: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(Path(__file__).resolve().parent / ".env")

        def _bool(name: str, default: str) -> bool:
            return os.getenv(name, default).strip().lower() in ("1", "true", "yes")

        login_url = os.getenv("LOGIN_URL", "").strip()
        if not login_url:
            raise SystemExit("LOGIN_URL no esta definido en el .env")

        return cls(
            login_url=login_url,
            headless=_bool("HEADLESS", "false"),
            patients_file=Path(os.getenv("PATIENTS_FILE", "data/patients.xlsx")),
            output_dir=Path(os.getenv("OUTPUT_DIR", "output")),
            date_format=os.getenv("DATE_FORMAT", "%d/%m/%Y"),
            login_timeout_ms=int(os.getenv("LOGIN_TIMEOUT_MS", "600000")),
            navigation_timeout_ms=int(os.getenv("NAVIGATION_TIMEOUT_MS", "60000")),
            modal_timeout_ms=int(os.getenv("MODAL_TIMEOUT_MS", "15000")),
            action_timeout_ms=int(os.getenv("ACTION_TIMEOUT_MS", "10000")),
            default_entidad=os.getenv("DEFAULT_ENTIDAD", "27 DE OCTUBRE"),
            perfil_entidad=os.getenv("PERFIL_ENTIDAD", "DIRECCION DISTRITAL 14D01"),
            search_fecha_desde=os.getenv("SEARCH_FECHA_DESDE", "").strip() or None,
            search_fecha_hasta=os.getenv("SEARCH_FECHA_HASTA", "").strip() or None,
            step_pause_ms=int(os.getenv("STEP_PAUSE_MS", "0")),
        )


@dataclass
class Patient:
    row: int
    ci: str
    entidad: str



_FAKE_NOMBRES = ["MARIA", "JOSE", "LUIS", "ANA", "CARLOS", "PAOLA", "DIEGO", "ELENA"]
_FAKE_APELLIDOS = ["PEREZ", "GOMEZ", "TORRES", "VEGA", "MOLINA", "ROJAS", "SOTO", "CEVALLOS"]
_FAKE_CIUDADES = ["QUITO", "GUAYAQUIL", "CUENCA", "AMBATO", "MANTA"]
_FAKE_PROVINCIAS = ["PICHINCHA", "GUAYAS", "AZUAY", "TUNGURAHUA", "MANABI"]


def _generar_cedula_ecuatoriana_valida() -> str:
    """Genera una cedula ecuatoriana de 10 digitos con digito verificador valido."""
    provincia = random.randint(1, 24)
    tercer_digito = random.randint(0, 6)
    digitos = [provincia // 10, provincia % 10, tercer_digito] + [
        random.randint(0, 9) for _ in range(6)
    ]
    coeficientes = [2, 1, 2, 1, 2, 1, 2, 1, 2]
    total = 0
    for digito, coef in zip(digitos, coeficientes):
        valor = digito * coef
        if valor >= 10:
            valor -= 9
        total += valor
    verificador = (10 - (total % 10)) % 10
    digitos.append(verificador)
    return "".join(str(d) for d in digitos)


def generate_fake_patients_file(
    path: Path, count: int, entidad: str, fixed_ci: str | None = None
) -> None:
    """Crea un xlsx de prueba con columnas A..M, donde A=CI y M=Entidad.

    Si fixed_ci se especifica, genera un unico paciente con esa CI exacta
    (el resto de columnas siguen siendo mockeadas) en vez de CIs aleatorias.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "pacientes"

    headers = [
        "Numero de Identificacion",  # A
        "Nombres",                   # B
        "Apellidos",                 # C
        "Fecha Nacimiento",          # D
        "Telefono",                  # E
        "Email",                     # F
        "Direccion",                 # G
        "Ciudad",                    # H
        "Provincia",                 # I
        "Genero",                    # J
        "Estado Civil",              # K
        "Observaciones",             # L
        "Entidad",                   # M
    ]
    ws.append(headers)

    ci_list = [fixed_ci] if fixed_ci else [_generar_cedula_ecuatoriana_valida() for _ in range(count)]

    for ci in ci_list:
        nombres = random.choice(_FAKE_NOMBRES)
        apellidos = random.choice(_FAKE_APELLIDOS)
        ws.append(
            [
                ci,
                nombres,
                apellidos,
                date(random.randint(1960, 2005), random.randint(1, 12), random.randint(1, 28)),
                f"09{random.randint(10000000, 99999999)}",
                f"{nombres.lower()}.{apellidos.lower()}@example.test",
                "DIRECCION DE PRUEBA S/N",
                random.choice(_FAKE_CIUDADES),
                random.choice(_FAKE_PROVINCIAS),
                random.choice(["M", "F"]),
                random.choice(["SOLTERO", "CASADO", "DIVORCIADO"]),
                "DATO DE PRUEBA - NO REAL",
                entidad,
            ]
        )

    wb.save(path)
    log.info("Archivo de pacientes fake generado en %s (%d filas)", path, len(ci_list))


def load_patients(path: Path, default_entidad: str) -> list[Patient]:
    if not path.exists():
        raise FileNotFoundError(
            f"No existe {path}. Genera datos de prueba con --generate-fake-data."
        )

    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb.active

    patients: list[Patient] = []
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        if not row or row[0] in (None, ""):
            continue
        ci = str(row[0]).strip()
        entidad = str(row[12]).strip() if len(row) > 12 and row[12] else default_entidad
        patients.append(Patient(row=row_idx, ci=ci, entidad=entidad))

    if not patients:
        raise ValueError(f"{path} no tiene filas de pacientes validas.")

    log.info("Cargados %d pacientes desde %s", len(patients), path)
    return patients



def scroll_page(page: Page, pixels: int = 700) -> None:
    page.mouse.wheel(0, pixels)
    page.wait_for_timeout(300)


def pause(page: Page, settings: Settings) -> None:
    """Pausa configurable (STEP_PAUSE_MS) entre pasos, para validar visualmente
    cada etapa del flujo en modo no-headless. 0 (default) no pausa nada."""
    if settings.step_pause_ms > 0:
        page.wait_for_timeout(settings.step_pause_ms)


def wait_for_modal(page: Page, timeout_ms: int) -> Locator:
    """Auto-wait: espera a que aparezca un modal visible y lo retorna."""
    modal = page.locator(MODAL_SELECTOR).last
    modal.wait_for(state="visible", timeout=timeout_ms)
    return modal


def wait_for_named_modal(page: Page, text: str, timeout_ms: int) -> Locator:
    """Espera un modal visible que contenga un texto especifico.

    [VERIFICADO EN VIVO] el sitio a veces apila mas de un modal con las
    mismas clases (".modal.in") al mismo tiempo: un spinner transitorio
    "Procesando, por favor espere..." junto al modal real (ej. "Impresiones"
    o "Visualizar archivo"). wait_for_modal() (".last" visible, sin filtro)
    puede agarrar el spinner en vez del modal correcto segun el orden en el
    DOM, causando fallos intermitentes mas adelante. Filtrar por texto evita
    la ambiguedad.
    """
    modal = page.locator(MODAL_SELECTOR).filter(has_text=text).last
    modal.wait_for(state="visible", timeout=timeout_ms)
    return modal


def close_modal_if_open(page: Page, timeout_ms: int) -> None:
    modal = page.locator(MODAL_SELECTOR).last
    if modal.count() == 0:
        return
    try:
        if modal.is_visible():
            page.keyboard.press("Escape")
            modal.wait_for(state="hidden", timeout=timeout_ms)
    except Exception:
        pass


def fill_and_verify(locator: Locator, value: str, field_label: str) -> None:
    """Llena un input y confirma que el valor quedo puesto. Varios campos de
    este formulario se resetean si otro campo cercano dispara un redibujado
    (ver select_entidad_chosen); esto convierte ese reseteo silencioso en un
    error explicito en vez de una busqueda con datos incompletos."""
    locator.fill(value)
    actual = locator.input_value()
    if actual != value:
        raise RuntimeError(
            f"El campo '{field_label}' quedo en '{actual}' en vez de "
            f"'{value}' tras llenarlo (el sitio parece resetear el campo)."
        )


def set_date_picker_field(
    page: Page, selector: str, value: date, settings: Settings, field_label: str
) -> None:
    """Fija una fecha en un input bootstrap-datepicker (jQuery "date-picker",
    data-date-format="dd-mm-yyyy") usando la API oficial del plugin
    (datepicker('setDate', Date)), no fill() ni tecleado.

    [VERIFICADO EN VIVO] tanto fill() como escribir caracter por caracter
    (press_sequentially) dejan el <input> con el texto visualmente correcto,
    pero la fecha INTERNA del widget (datepicker('getDate')) queda
    desincronizada (null). En algun momento posterior (blur, cierre del
    popup) el propio widget reescribe el campo con su fecha interna, que por
    defecto es "hoy" -- confirmado en vivo: el campo terminaba con la fecha
    del dia en vez de la tecleada. datepicker('setDate', Date) es la API
    propia del plugin y deja texto + estado interno sincronizados en un solo
    paso, sin depender de la secuencia de eventos de teclado/foco.
    """
    page.evaluate(
        "(args) => { const [sel, y, m, d] = args; "
        "window.jQuery(sel).datepicker('setDate', new Date(y, m, d)); }",
        [selector, value.year, value.month - 1, value.day],
    )
    actual = page.locator(selector).input_value()
    expected = value.strftime(settings.date_format)
    if actual != expected:
        raise RuntimeError(
            f"El campo '{field_label}' quedo en '{actual}' en vez de "
            f"'{expected}' tras fijarlo con datepicker('setDate', ...)."
        )


def select_entidad_chosen(page: Page, select_locator: Locator, target_text: str) -> None:
    """Selecciona una opcion en el <select> de jQuery Chosen (class
    "chosen-select") replicando la interaccion real de un usuario: click
    para abrir el widget visual, escribir en su buscador y click en el
    resultado filtrado. El <select> nativo queda oculto por Chosen (por
    eso no se interactua con el directamente); Chosen inserta su widget
    como el siguiente elemento hermano del <select> original.
    """
    container = select_locator.locator(
        "xpath=following-sibling::*[contains(@class,'chosen-container')][1]"
    )
    container.locator(".chosen-single").click()

    search_input = container.locator(".chosen-search input")
    search_input.fill(target_text)

    result = container.locator("li.active-result", has_text=target_text).first
    result.click()



def assisted_login(page: Page, settings: Settings) -> None:
    log.info("Abriendo %s - inicia sesion manualmente en la ventana de Chromium...", settings.login_url)
    page.goto(settings.login_url, wait_until="domcontentloaded", timeout=settings.navigation_timeout_ms)

    initial_url = page.url
    log.info(
        "Pagina de login cargada (%s). Esperando hasta %d min a que inicies sesion manualmente...",
        initial_url,
        settings.login_timeout_ms // 60000,
    )

    try:
        page.wait_for_url(lambda url: url != initial_url, timeout=settings.login_timeout_ms)
    except Exception as exc:
        raise RuntimeError(
            "No se detecto un cambio de URL tras el login dentro de "
            f"{settings.login_timeout_ms}ms. Si el sitio es una SPA que no "
            "cambia de URL al loguearse, avisa para cambiar la deteccion "
            "por un selector especifico del home."
        ) from exc

    page.wait_for_load_state("domcontentloaded", timeout=settings.navigation_timeout_ms)

    password_field = page.locator('input[type="password"]')
    if password_field.count() > 0 and password_field.first.is_visible():
        raise RuntimeError(
            f"La URL cambio a {page.url} pero todavia se ve un campo de "
            "contraseña visible: el login parece no haberse completado."
        )

    log.info("Login confirmado (URL: %s, sin campo de contraseña visible).", page.url)

    page.wait_for_timeout(2000)


def open_mis_perfiles_menu(page: Page, settings: Settings) -> None:
    """[VERIFICADO EN VIVO] Si la cuenta ya tiene un rol activo de una sesion
    anterior, el sitio no muestra ni la tarjeta "Reportes" ni el modal de
    seleccion: aterriza directo en el dashboard de ese rol (que puede no ser
    el que necesita este script, ej. "MEDICO - ADMISION..." en vez de
    "ESPECIALISTA DISTRITAL..."). Se fuerza la reapertura del modal via el
    menu de usuario (esquina superior derecha, clase ACE Admin
    "dropdown-modal") -> "Mis Perfiles", que abre el mismo modal (misma
    tabla Nombre/Entidad/Seleccione y boton Guardar) que "Acceder" en la
    tarjeta Reportes."""
    page.locator("li.dropdown-modal > a.dropdown-toggle").first.click()
    page.get_by_role("link", name="Mis Perfiles", exact=True).click()
    wait_for_modal(page, settings.modal_timeout_ms)


def open_reportes_card(page: Page, settings: Settings) -> None:
    scroll_page(page)
    page.wait_for_timeout(1000)
    modal = page.locator(MODAL_SELECTOR).last
    if modal.count() > 0 and modal.is_visible():
        log.info("El modal de seleccion de perfil ya estaba abierto, se omite el click en Acceder.")
        return

    reportes_card = page.locator("div", has_text="Reportes").filter(
        has=page.get_by_role("button", name="Acceder")
    ).last
    if reportes_card.count() > 0 and reportes_card.is_visible():
        acceder_btn = reportes_card.get_by_role("button", name="Acceder")
        acceder_btn.click()
        page.wait_for_timeout(1000)
        wait_for_modal(page, settings.modal_timeout_ms)
        return

    log.warning(
        "No aparecio la tarjeta 'Reportes' ni el modal (probable rol ya "
        "activo de una sesion anterior de la misma cuenta). Forzando el "
        "modal de seleccion de rol via el menu 'Mis Perfiles'."
    )
    open_mis_perfiles_menu(page, settings)


def select_role_and_save(page: Page, settings: Settings) -> None:
    modal = wait_for_modal(page, settings.modal_timeout_ms)

    modal.get_by_text("Nombre", exact=True).first.click()

    fila = modal.locator(
        "tr", has_text="ESPECIALISTA DISTRITAL CALIDAD DE LOS SERVICIOS DE SALUD"
    ).filter(has_text=settings.perfil_entidad).first
    fila.locator('input[type="radio"]').check(force=True)

    scroll_page(page, 400)

    modal.get_by_role("button", name="Guardar").click()

    close_modal_if_open(page, settings.modal_timeout_ms)


def open_historial_atenciones(page: Page, settings: Settings) -> None:
    nav_btn = page.get_by_role("link", name="Reportes Administrativos")
    nav_btn.click()
    page.get_by_text("Historial Atenciones", exact=True).click()

    modal = wait_for_modal(page, settings.modal_timeout_ms)
    scroll_page(page, 300)

    modal.get_by_role("button", name="Aceptar").click()
    close_modal_if_open(page, settings.modal_timeout_ms)


def search_patient(page: Page, patient: Patient, settings: Settings) -> None:

    if settings.search_fecha_desde and settings.search_fecha_hasta:
        fecha_desde = datetime.strptime(settings.search_fecha_desde, settings.date_format).date()
        fecha_hasta = datetime.strptime(settings.search_fecha_hasta, settings.date_format).date()
    else:
        today = date.today()
        fecha_desde = today.replace(day=1)
        fecha_hasta = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    entidad_select = page.locator('select[name="select-entidad"]')
    select_entidad_chosen(page, entidad_select, patient.entidad)

    set_date_picker_field(page, 'input[name="paciente_fecha_desde"]', fecha_desde, settings, "Desde")

    set_date_picker_field(page, 'input[name="paciente_fecha_hasta"]', fecha_hasta, settings, "Hasta")

    fill_and_verify(
        page.locator("#paciente_numeroidentificacion"), patient.ci, "Número Identificación"
    )

    page.locator("#searchpacientedatatble-button").click()

    scroll_page(page, 500)


def select_result_row(page: Page, settings: Settings, patient: Patient) -> None:

    row_cell = page.locator('td[tabindex="0"]').first
    empty_state = page.locator("td.dataTables_empty").first

    try:
        row_cell.or_(empty_state).wait_for(state="visible", timeout=settings.action_timeout_ms)
    except Exception as exc:
        raise RuntimeError(
            f"La tabla de resultados no mostro ninguna fila ni el estado "
            f"'sin resultados' dentro de {settings.action_timeout_ms}ms "
            f"para CI={patient.ci}. Revisa el estado de la busqueda "
            "manualmente (¿parametros de fecha/entidad correctos?)."
        ) from exc

    if empty_state.is_visible():
        raise RuntimeError(
            f"Sin resultados: no se encontraron atenciones para CI={patient.ci} "
            f"entidad={patient.entidad} en el rango de fechas configurado."
        )

    row_cell.click()

    child_row = row_cell.locator(
        "xpath=ancestor::tr[1]/following-sibling::tr[contains(@class,'child')][1]"
    )
    pdf_icon = child_row.locator("i.fa.fa-file-pdf-o.bigger-125.fa-fw.red").first
    pdf_icon.wait_for(state="visible", timeout=settings.action_timeout_ms)
    pdf_icon.click()


def fill_motivo_and_save(page: Page, settings: Settings) -> None:
    modal = wait_for_modal(page, settings.modal_timeout_ms)

    modal.locator("#impresatencionmedica_ctmotivo").select_option(value="3088")

    modal.locator("#impresatencionmedica_observacion").fill("RCPROVINCIAL")

    modal.get_by_role("button", name="Guardar").click()

    wait_for_named_modal(page, "Impresiones", settings.modal_timeout_ms)


def print_atencion_and_extract_pdf(
    page: Page, settings: Settings, patient: Patient
) -> Path:
    page.locator('button[onclick="printatencionAction()"]').click()

    modal = wait_for_named_modal(page, "Visualizar archivo", settings.modal_timeout_ms)

    pdf_bytes = _extract_pdf_bytes_from_modal(page, modal)

    settings.output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdf_path = settings.output_dir / f"atencion_{patient.ci}_{timestamp}.pdf"
    pdf_path.write_bytes(pdf_bytes)

    text = _extract_text_from_pdf_bytes(pdf_bytes)
    txt_path = pdf_path.with_suffix(".txt")
    txt_path.write_text(text, encoding="utf-8")

    log.info("PDF guardado en %s (texto extraido en %s)", pdf_path, txt_path)

    close_modal_if_open(page, settings.modal_timeout_ms)
    return pdf_path


def _extract_pdf_bytes_from_modal(page: Page, modal: Locator) -> bytes:
    """Obtiene los bytes del PDF mostrado en el modal via Playwright (sin CLI)."""
    viewer = modal.locator("iframe, embed, object").first
    viewer.wait_for(state="attached", timeout=15000)

    src = viewer.get_attribute("src") or viewer.get_attribute("data") or ""
    if not src:
        raise RuntimeError("No se encontro el visor de PDF (iframe/embed/object) en el modal.")

    if src.startswith("data:application/pdf;base64,"):
        import base64

        return base64.b64decode(src.split(",", 1)[1])

    absolute_url = urljoin(page.url, src)
    response = page.context.request.get(absolute_url)
    if not response.ok:
        raise RuntimeError(f"No se pudo descargar el PDF ({response.status}) desde {absolute_url}")
    return response.body()


def _extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page_obj in pdf.pages:
            text_parts.append(page_obj.extract_text() or "")
    return "\n".join(text_parts).strip()


def ensure_chromium_installed(chromium: BrowserType) -> None:
    """Verifica el binario de Chromium de Playwright y lo instala si falta.

    Permite correr el script en una PC nueva sin el paso manual de
    'playwright install chromium'.
    """
    executable = Path(chromium.executable_path)
    if executable.exists():
        return

    log.warning("Chromium de Playwright no encontrado en %s. Instalando...", executable)
    result = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])

    if result.returncode != 0 or not executable.exists():
        raise SystemExit(
            "No se pudo instalar Chromium automaticamente. "
            "Corre manualmente: python -m playwright install chromium"
        )
    log.info("Chromium instalado correctamente.")


def process_patient(page: Page, settings: Settings, patient: Patient) -> None:
    log.info("Procesando paciente CI=%s entidad=%s", patient.ci, patient.entidad)
    search_patient(page, patient, settings)
    pause(page, settings)
    select_result_row(page, settings, patient)
    pause(page, settings)
    fill_motivo_and_save(page, settings)
    pause(page, settings)
    print_atencion_and_extract_pdf(page, settings, patient)
    pause(page, settings)


def run(settings: Settings) -> None:
    patients = load_patients(settings.patients_file, settings.default_entidad)

    with sync_playwright() as pw:

        ensure_chromium_installed(pw.chromium)
        browser = pw.chromium.launch(headless=settings.headless)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(settings.action_timeout_ms)

        try:
            assisted_login(page, settings)
            pause(page, settings)
            open_reportes_card(page, settings)
            pause(page, settings)
            select_role_and_save(page, settings)
            pause(page, settings)
            open_historial_atenciones(page, settings)
            pause(page, settings)

            for patient in patients:
                close_modal_if_open(page, settings.modal_timeout_ms)
                process_patient(page, settings, patient)

        finally:
            context.close()
            browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generate-fake-data",
        action="store_true",
        help="Genera un xlsx de pacientes de prueba (datos ficticios) y termina.",
    )
    parser.add_argument("--count", type=int, default=5, help="Numero de pacientes fake a generar.")
    parser.add_argument(
        "--ci",
        type=str,
        default=None,
        help="Genera un unico paciente con esta CI exacta en vez de CIs aleatorias.",
    )
    parser.add_argument("--run", action="store_true", help="Corre la automatizacion completa.")
    args = parser.parse_args()

    settings = Settings.from_env()

    if args.generate_fake_data:
        generate_fake_patients_file(
            settings.patients_file, args.count, settings.default_entidad, fixed_ci=args.ci
        )
        return

    if not settings.patients_file.exists():
        log.warning("%s no existe, generando datos de prueba automaticamente.", settings.patients_file)
        generate_fake_patients_file(
            settings.patients_file, args.count, settings.default_entidad, fixed_ci=args.ci
        )

    if args.run or not args.generate_fake_data:
        run(settings)


if __name__ == "__main__":
    main()
