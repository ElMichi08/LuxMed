from __future__ import annotations
import sys
import time
from pathlib import Path
from datetime import date, datetime

import logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(name)s] %(levelname)s: %(message)s",
)
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

import pandas as pd

PACIENTES = [
    {
        "NOMBRE Y APELLIDOS": "CHACHA FERNANDEZ JHULIAN ESTIVEN",
        "CEDULA": "1450111008",
        "FECHA NACIMIENTO": "22/02/2013",
        "APORTA": "IESS, Afiliado seguro Campesino",
        "FECHA ATENCION": "23/04/2026",
        "NOM ESTABLECIMIENTO": "27 DE FEBRERO",
    },
    {
        "NOMBRE Y APELLIDOS": "CASTRO FAJARDO JULIETTA ANTONELLA",
        "CEDULA": "1450920150",
        "FECHA NACIMIENTO": "05/11/2025",
        "APORTA": "IESS, Dependiente hijo menor de 18 años de afiliado al seguro general",
        "FECHA ATENCION": "06/04/2026",
        "NOM ESTABLECIMIENTO": "27 DE FEBRERO",
    },
    {
        "NOMBRE Y APELLIDOS": "JUA YURANGUI ALISIA FLORA",
        "CEDULA": "1400303796",
        "FECHA NACIMIENTO": "25/10/1970",
        "APORTA": "IESS, Afiliado seguro general tiempo completo",
        "FECHA ATENCION": "14/04/2026",
        "NOM ESTABLECIMIENTO": "CENTRO DE SALUD INNFA 24HD",
    },
    {
        "NOMBRE Y APELLIDOS": "OCHOA CHUNO CESAR RENE",
        "CEDULA": "1400372825",
        "FECHA NACIMIENTO": "27/03/1973",
        "APORTA": "IESS, Afiliado voluntario",
        "FECHA ATENCION": "30/04/2026",
        "NOM ESTABLECIMIENTO": "CENTRO DE SALUD INNFA 24HD",
    },
    {
        "NOMBRE Y APELLIDOS": "GAVILANES SILVA MATHIAS DANIEL",
        "CEDULA": "1650437211",
        "FECHA NACIMIENTO": "23/05/2024",
        "APORTA": "Seguro ISSPOL",
        "FECHA ATENCION": "15/04/2026",
        "NOM ESTABLECIMIENTO": "27 DE FEBRERO",
    },
    {
        "NOMBRE Y APELLIDOS": "CANGUA CALLE WILLIAN ALEXIS",
        "CEDULA": "1450847015",
        "FECHA NACIMIENTO": "04/04/2024",
        "APORTA": "Seguro ISSFA",
        "FECHA ATENCION": "09/04/2026",
        "NOM ESTABLECIMIENTO": "SANTA ROSA",
    },
]

INPUT_DIR = BASE_DIR / "data" / "input"
OUTPUT_DIR = BASE_DIR / "data" / "output"
PDF_DIR = OUTPUT_DIR / "pdfs"

INPUT_EXCEL = INPUT_DIR / "pacientes_prueba.xlsx"


def crear_excel_entrada() -> Path:
    """Crea el Excel de entrada con los 6 pacientes de prueba."""
    INPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(PACIENTES)
    df.to_excel(INPUT_EXCEL, sheet_name="BASE", index=False)
    print(f"[OK] Excel de entrada creado: {INPUT_EXCEL}")
    print(f"   -> {len(PACIENTES)} pacientes cargados")
    return INPUT_EXCEL


def ejecutar_flujo():

    # ── Imports del proyecto ──
    from app.infrastructure.excel.excel_handler import ExcelHandler
    from app.infrastructure.scraper.playwright_scraper import Portal1Adapter
    from app.infrastructure.scraper.portal3_adapter import Portal3Adapter
    from app.infrastructure.database.sqlite_adapter import SQLiteAdapter
    from app.infrastructure.pdf.pdf_merger import PdfConsolidatorAdapter
    from app.application.orchestrator import OrchestratorService
    from app.application.validator import ValidatorService

    # ── Paso 1: Crear Excel de entrada ──
    print("\n" + "=" * 60)
    print("  PASO 1: CREAR EXCEL DE ENTRADA")
    print("=" * 60)
    ruta_input = crear_excel_entrada()

    # ── Paso 2: Leer pacientes del Excel ──
    print("\n" + "=" * 60)
    print("  PASO 2: LEER PACIENTES DEL EXCEL")
    print("=" * 60)
    excel_handler = ExcelHandler()
    pacientes = excel_handler.leer_pacientes(str(ruta_input))
    print(f"[OK] {len(pacientes)} pacientes leidos del Excel")
    for i, p in enumerate(pacientes, 1):
        print(f"   {i}. {p.nombre_y_apellidos} ({p.cedula}) - {p.aporta}")

    # ── Paso 3: Higienizar y clasificar ──
    print("\n" + "=" * 60)
    print("  PASO 3: HIGIENIZAR Y CLASIFICAR")
    print("=" * 60)
    validator = ValidatorService()
    for p in pacientes:
        validator.higienizar_y_clasificar(p)
    print("[OK] Pacientes higienizados y clasificados")

    # ── Paso 4: Guardar en SQLite ──
    print("\n" + "=" * 60)
    print("  PASO 4: GUARDAR EN SQLite")
    print("=" * 60)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    db_path = OUTPUT_DIR / "luxmed_test.db"
    repo = SQLiteAdapter(str(db_path))
    repo.guardar_lote(pacientes)
    print(f"[OK] {len(pacientes)} pacientes guardados en {db_path}")

    # ── Paso 5: Configurar Scraper (headless=False, ventanas off-screen) ──
    print("\n" + "=" * 60)
    print("  PASO 5: CONFIGURAR SCRAPER")
    print("=" * 60)
    from app.infrastructure.scraper.portal2_iess_adapter import Portal2IessAdapter
    from app.infrastructure.scraper.altcha_handler import AltchaHandler
    portal2 = Portal2IessAdapter(altcha_handler=AltchaHandler(), headless=False)
    scraper = Portal1Adapter(headless=False, portal2_adapter=portal2)
    print("[OK] Scraper configurado con headless=False (ventanas off-screen)")
    print("[OK] Portal 2 (IESS) conectado al scraper")

    # ── Paso 6: Configurar Portal 3 (login automático por cada paciente) ──
    portal3 = Portal3Adapter(headless=False)

    # ── Paso 7: Configurar consolidador de PDFs ──
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    pdf_consolidator = PdfConsolidatorAdapter(str(PDF_DIR))

    # ── Paso 8: Crear orquestador ──
    print("\n" + "=" * 60)
    print("  PASO 6: CREAR ORQUESTADOR")
    print("=" * 60)
    orch = OrchestratorService(
        repository=repo,
        scraper=scraper,
        pdf_consolidator=pdf_consolidator,
        portal3_adapter=portal3,
        excel_handler=excel_handler,
    )
    print("[OK] Orquestador creado con todas las dependencias")

    # ── Paso 9: Procesar cola ──
    print("\n" + "=" * 60)
    print("  PASO 7: PROCESAR COLA DE PACIENTES")
    print("=" * 60)
    print("[INICIANDO] Procesamiento...")
    print("   -> Se abrira Chromium para cada paciente")
    print("   -> Puedes ver el proceso en pantalla")
    print()

    inicio = time.time()
    pacientes_procesados = orch.procesar_cola()
    duracion = time.time() - inicio

    print(f"\n[OK] Procesamiento completado en {duracion:.1f} segundos")

    # ── Paso 10: Guardar PDFs consolidados ──
    print("\n" + "=" * 60)
    print("  PASO 8: GUARDAR PDFs CONSOLIDADOS")
    print("=" * 60)
    pdfs_guardados = 0
    for p in pacientes_procesados:
        ruta_pdf = pdf_consolidator.guardar(p)
        if ruta_pdf:
            pdfs_guardados += 1
            print(f"   PDF: {ruta_pdf.name}")

    print(f"\n[OK] {pdfs_guardados} PDFs guardados en {PDF_DIR}")

    # ── Paso 11: Generar Excels de salida ──
    print("\n" + "=" * 60)
    print("  PASO 9: GENERAR EXCELS DE SALIDA")
    print("=" * 60)
    ruta_limpio = OUTPUT_DIR / "pacientes_limpio.xlsx"
    ruta_auditoria = OUTPUT_DIR / "pacientes_auditoria.xlsx"

    orch.generar_excels(
        pacientes=pacientes_procesados,
        ruta_origen=str(ruta_input),
        ruta_limpio=str(ruta_limpio),
        ruta_auditoria=str(ruta_auditoria),
    )
    print(f"[OK] Excel limpio: {ruta_limpio}")
    print(f"[OK] Excel auditoria: {ruta_auditoria}")

    # ── Paso 12: Resumen final ──
    print("\n" + "=" * 60)
    print("  RESUMEN FINAL")
    print("=" * 60)
    print("   Carpetas creadas:")
    print("   |-- data/input/")
    print("   |   +-- pacientes_prueba.xlsx")
    print("   |-- data/output/")
    print("   |   +-- pacientes_limpio.xlsx")
    print("   |   +-- pacientes_auditoria.xlsx")
    print("   |   +-- luxmed_test.db")
    print("   |   +-- pdfs/ (%d archivos)" % pdfs_guardados)
    print("   +-- cookies_portal3.json")
    print()

    # ── Detalle por paciente ──
    print("DETALLE POR PACIENTE:")
    for p in pacientes_procesados:
        status = "[VALIDO]" if p.estado.value == "VALIDO" else "[INVALIDO]"
        pdfs = []
        if p.pdf_p1_propio_bytes:
            pdfs.append(f"P1 propio ({len(p.pdf_p1_propio_bytes)} bytes)")
        if p.pdf_p1_acreditador_bytes:
            pdfs.append(f"P1 acreditador ({len(p.pdf_p1_acreditador_bytes)} bytes)")
        if p.pdf_p3_bytes:
            pdfs.append(f"P3 ({len(p.pdf_p3_bytes)} bytes)")
        if p.pdf_consolidado:
            pdfs.append(f"consolidado ({len(p.pdf_consolidado)} bytes)")

        pdf_str = ", ".join(pdfs) if pdfs else "sin PDFs"
        print(f"   {p.cedula} - {p.nombre_y_apellidos}")
        print(f"      Estado: {status} | Entidad: {p.entidad_detectada.value}")
        print(f"      PDFs: {pdf_str}")
        if p.cedula_acreditador:
            print(f"      Acreditador: {p.cedula_acreditador}")
        print()

    print("FLUJO COMPLETO FINALIZADO!")
    return pacientes_procesados


if __name__ == "__main__":
    try:
        ejecutar_flujo()
    except KeyboardInterrupt:
        print("\n\n[INTERRUMPIDO] Proceso interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
