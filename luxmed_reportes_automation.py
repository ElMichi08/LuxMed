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
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pdfplumber
from dotenv import load_dotenv
from openpyxl import Workbook, load_workbook
from playwright.sync_api import Locator, Page, sync_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("luxmed_automation")

MODAL_SELECTOR = ".modal.show, .modal.in"


# --------------------------------------------------------------------------
# Configuracion
# --------------------------------------------------------------------------

@dataclass
class Settings:
    login_url: str
    headless: bool
    patients_file: Path
    output_dir: Path
    date_format: str
    login_timeout_ms: int
    modal_timeout_ms: int
    action_timeout_ms: int
    default_entidad: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

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
            modal_timeout_ms=int(os.getenv("MODAL_TIMEOUT_MS", "15000")),
            action_timeout_ms=int(os.getenv("ACTION_TIMEOUT_MS", "10000")),
            default_entidad=os.getenv("DEFAULT_ENTIDAD", "27 DE OCTUBRE"),
        )


@dataclass
class Patient:
    row: int
    ci: str
    entidad: str


# --------------------------------------------------------------------------
# Datos de prueba (fake) - nunca datos reales de pacientes
# --------------------------------------------------------------------------

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


def generate_fake_patients_file(path: Path, count: int, entidad: str) -> None:
    """Crea un xlsx de prueba con columnas A..M, donde A=CI y M=Entidad."""
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

    for _ in range(count):
        nombres = random.choice(_FAKE_NOMBRES)
        apellidos = random.choice(_FAKE_APELLIDOS)
        ws.append(
            [
                _generar_cedula_ecuatoriana_valida(),
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
    log.info("Archivo de pacientes fake generado en %s (%d filas)", path, count)


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
        # Columna M = indice 12 (0-based)
        entidad = str(row[12]).strip() if len(row) > 12 and row[12] else default_entidad
        patients.append(Patient(row=row_idx, ci=ci, entidad=entidad))

    if not patients:
        raise ValueError(f"{path} no tiene filas de pacientes validas.")

    log.info("Cargados %d pacientes desde %s", len(patients), path)
    return patients


# --------------------------------------------------------------------------
# Helpers de UI
# --------------------------------------------------------------------------

def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text.strip().upper()


def scroll_page(page: Page, pixels: int = 700) -> None:
    page.mouse.wheel(0, pixels)
    page.wait_for_timeout(300)


def wait_for_modal(page: Page, timeout_ms: int) -> Locator:
    """Auto-wait: espera a que aparezca un modal visible y lo retorna."""
    modal = page.locator(MODAL_SELECTOR).last
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


def select_option_by_text(select_locator: Locator, target_text: str) -> None:
    """Selecciona la <option> cuyo texto visible coincide (normalizado) con target_text."""
    target = _normalize(target_text)
    options = select_locator.locator("option")
    count = options.count()
    for i in range(count):
        option = options.nth(i)
        if _normalize(option.inner_text()) == target:
            value = option.get_attribute("value")
            select_locator.select_option(value=value)
            return
    # Fallback: coincidencia parcial
    for i in range(count):
        option = options.nth(i)
        if target in _normalize(option.inner_text()):
            value = option.get_attribute("value")
            select_locator.select_option(value=value)
            return
    raise ValueError(f"No se encontro la opcion '{target_text}' en el select.")


# --------------------------------------------------------------------------
# Pasos del flujo
# --------------------------------------------------------------------------

def assisted_login(page: Page, settings: Settings) -> None:
    log.info("Abriendo %s - inicia sesion manualmente en la ventana de Chromium...", settings.login_url)
    page.goto(settings.login_url)

    # [HEURISTICO] Se asume que el home muestra una tarjeta "Reportes" con
    # boton "Acceder". Se usa como senal de que el login se completo.
    home_marker = page.get_by_role("button", name="Acceder").first
    home_marker.wait_for(state="visible", timeout=settings.login_timeout_ms)
    log.info("Login detectado, continuando con la automatizacion.")


def open_reportes_card(page: Page, settings: Settings) -> None:
    scroll_page(page)
    # [HEURISTICO] boton "Acceder" dentro de la tarjeta "Reportes"
    reportes_card = page.locator("div", has_text="Reportes").filter(
        has=page.get_by_role("button", name="Acceder")
    ).last
    acceder_btn = reportes_card.get_by_role("button", name="Acceder")
    acceder_btn.click()

    wait_for_modal(page, settings.modal_timeout_ms)


def select_role_and_save(page: Page, settings: Settings) -> None:
    modal = wait_for_modal(page, settings.modal_timeout_ms)

    # [EXACTO por texto de usuario] click en columna "Nombre" (encabezado de tabla)
    modal.get_by_text("Nombre", exact=True).first.click()

    # [EXACTO] radio button de la fila con este texto
    fila = modal.locator(
        "tr", has_text="ESPECIALISTA DISTRITAL CALIDAD DE LOS SERVICIOS DE SALUD"
    ).first
    fila.locator('input[type="radio"]').click()

    scroll_page(page, 400)

    # [EXACTO] boton Guardar del modal
    modal.get_by_role("button", name="Guardar").click()

    close_modal_if_open(page, settings.modal_timeout_ms)


def open_historial_atenciones(page: Page, settings: Settings) -> None:
    # [HEURISTICO] boton en la barra superior "Reportes Administrativos"
    nav_btn = page.get_by_role("button", name="Reportes Administrativos")
    nav_btn.click()

    # [EXACTO por texto de usuario] unica opcion por ahora: "Historial de Atenciones"
    page.get_by_text("Historial de Atenciones", exact=False).click()

    modal = wait_for_modal(page, settings.modal_timeout_ms)
    scroll_page(page, 300)

    # [EXACTO] boton Aceptar del modal
    modal.get_by_role("button", name="Aceptar").click()
    close_modal_if_open(page, settings.modal_timeout_ms)


def search_patient(page: Page, patient: Patient, settings: Settings) -> None:
    today = date.today()
    first_day = today.replace(day=1)
    last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    # [EXACTO] input con placeholder "Numero de Identificacion"
    ci_input = page.get_by_placeholder("Numero de Identificacion")
    ci_input.fill(patient.ci)

    # [EXACTO] input name="paciente_fecha_desde"
    page.locator('input[name="paciente_fecha_desde"]').fill(
        first_day.strftime(settings.date_format)
    )

    # [EXACTO] input name="paciente_fecha_hasta"
    page.locator('input[name="paciente_fecha_hasta"]').fill(
        last_day.strftime(settings.date_format)
    )

    # [EXACTO] select name="select-entidad"
    entidad_select = page.locator('select[name="select-entidad"]')
    select_option_by_text(entidad_select, patient.entidad)

    # [EXACTO] boton id=searchpacientedatatble-button
    page.locator("#searchpacientedatatble-button").click()

    scroll_page(page, 500)


def select_result_row(page: Page, settings: Settings) -> None:
    # [EXACTO] <td tabindex="0"> de la fila resultante (contenido variable)
    row_cell = page.locator('td[tabindex="0"]').first
    row_cell.wait_for(state="visible", timeout=settings.action_timeout_ms)
    row_cell.click()

    # [EXACTO] icono pdf rojo que aparece tras seleccionar la fila
    pdf_icon = page.locator("i.fa.fa-file-pdf-o.bigger-125.fa-fw.red").first
    pdf_icon.wait_for(state="visible", timeout=settings.action_timeout_ms)
    pdf_icon.click()


def fill_motivo_and_save(page: Page, settings: Settings) -> None:
    modal = wait_for_modal(page, settings.modal_timeout_ms)

    # [EXACTO] select id=impresatencionmedica_ctmotivo -> option value=3088 (Otros)
    modal.locator("#impresatencionmedica_ctmotivo").select_option(value="3088")

    # [EXACTO] textarea id=impresatencionmedica_observacion
    modal.locator("#impresatencionmedica_observacion").fill("RCPROVINCIAL")

    # [EXACTO] boton "Guardar" (btn btn-sm btn-primary, icono ace-icon fa fa-check)
    modal.get_by_role("button", name="Guardar").click()

    wait_for_modal(page, settings.modal_timeout_ms)


def print_atencion_and_extract_pdf(
    page: Page, settings: Settings, patient: Patient
) -> Path:
    # [EXACTO] boton con onclick="printatencionAction()" title="Atencion"
    page.locator('button[onclick="printatencionAction()"]').click()

    modal = wait_for_modal(page, settings.modal_timeout_ms)

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

    absolute_url = src if src.startswith("http") else page.url.rsplit("/", 1)[0] + "/" + src.lstrip("/")
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


# --------------------------------------------------------------------------
# Orquestacion
# --------------------------------------------------------------------------

def process_patient(page: Page, settings: Settings, patient: Patient) -> None:
    log.info("Procesando paciente CI=%s entidad=%s", patient.ci, patient.entidad)
    search_patient(page, patient, settings)
    select_result_row(page, settings)
    fill_motivo_and_save(page, settings)
    print_atencion_and_extract_pdf(page, settings, patient)


def run(settings: Settings) -> None:
    patients = load_patients(settings.patients_file, settings.default_entidad)

    with sync_playwright() as pw:
        # Instancia propia y aislada de Chromium (modo test), no el navegador
        # personal del usuario.
        browser = pw.chromium.launch(headless=settings.headless)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(settings.action_timeout_ms)

        try:
            assisted_login(page, settings)
            open_reportes_card(page, settings)
            select_role_and_save(page, settings)
            open_historial_atenciones(page, settings)

            for patient in patients:
                close_modal_if_open(page, settings.modal_timeout_ms)
                process_patient(page, settings, patient)

        finally:
            context.close()
            browser.close()


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--generate-fake-data",
        action="store_true",
        help="Genera un xlsx de pacientes de prueba (datos ficticios) y termina.",
    )
    parser.add_argument("--count", type=int, default=5, help="Numero de pacientes fake a generar.")
    parser.add_argument("--run", action="store_true", help="Corre la automatizacion completa.")
    args = parser.parse_args()

    settings = Settings.from_env()

    if args.generate_fake_data:
        generate_fake_patients_file(settings.patients_file, args.count, settings.default_entidad)
        return

    if not settings.patients_file.exists():
        log.warning("%s no existe, generando datos de prueba automaticamente.", settings.patients_file)
        generate_fake_patients_file(settings.patients_file, args.count, settings.default_entidad)

    if args.run or not args.generate_fake_data:
        run(settings)


if __name__ == "__main__":
    main()
