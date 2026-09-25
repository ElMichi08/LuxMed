from __future__ import annotations

import sys
from pathlib import Path

from app.application.lote_service import FabricaOrquestador, ServicioLote
from app.application.orchestrator import OrchestratorService
from app.application.validator import ValidatorService
from app.domain.entities import CredencialesPortal3
from app.infrastructure.config.env_configuracion import EnvConfiguracionAdapter
from app.infrastructure.database.sqlite_adapter import SQLiteAdapter
from app.infrastructure.excel.excel_handler import ExcelHandler
from app.infrastructure.ui.bootstrap import ejecutar

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RUTA_ENV = BASE_DIR / ".env"
RUTA_DB = DATA_DIR / "luxmed.db"
CARPETA_SALIDA_POR_DEFECTO = DATA_DIR / "salidas"
CARPETA_LOGS = DATA_DIR / "logs"
MODO_HEADLESS = False


def crear_fabrica_orquestador(repositorio: SQLiteAdapter, excel: ExcelHandler) -> FabricaOrquestador:
    def fabricar(credenciales: CredencialesPortal3, carpeta_pdfs: str) -> OrchestratorService:
        from app.infrastructure.pdf.pdf_merger import PdfConsolidatorAdapter
        from app.infrastructure.scraper.altcha_handler import AltchaHandler
        from app.infrastructure.scraper.playwright_scraper import Portal1Adapter
        from app.infrastructure.scraper.portal2_iess_adapter import Portal2IessAdapter
        from app.infrastructure.scraper.portal3_adapter import Portal3Adapter

        portal2 = Portal2IessAdapter(
            altcha_handler=AltchaHandler(), headless=MODO_HEADLESS
        )
        return OrchestratorService(
            repository=repositorio,
            scraper=Portal1Adapter(headless=MODO_HEADLESS, portal2_adapter=portal2),
            pdf_consolidator=PdfConsolidatorAdapter(carpeta_pdfs),
            portal3_adapter=Portal3Adapter(
                headless=MODO_HEADLESS,
                usuario=credenciales.usuario,
                contrasena=credenciales.contrasena,
            ),
            excel_handler=excel,
        )

    return fabricar


def main() -> int:
    CARPETA_SALIDA_POR_DEFECTO.mkdir(parents=True, exist_ok=True)
    configuracion = EnvConfiguracionAdapter(RUTA_ENV, CARPETA_SALIDA_POR_DEFECTO)
    repositorio = SQLiteAdapter(str(RUTA_DB))
    excel = ExcelHandler()
    servicio = ServicioLote(
        excel=excel,
        repositorio=repositorio,
        validador=ValidatorService(),
        configuracion=configuracion,
        fabrica_orquestador=crear_fabrica_orquestador(repositorio, excel),
    )
    return ejecutar(servicio, configuracion, CARPETA_LOGS)


if __name__ == "__main__":
    sys.exit(main())
