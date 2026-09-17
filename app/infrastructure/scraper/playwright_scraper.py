from __future__ import annotations
import re
from datetime import date
from app.domain.ports import IScraperService
from app.domain.entities import Paciente
from app.infrastructure.scraper.portal_1_scrapper import scrape_cobertura, URL

# Entidades conocidas del portal de cobertura
ENTIDADES_CONOCIDAS = ["IESS", "ISSFA", "ISSPOL"]


class Portal1Adapter(IScraperService):
    def __init__(
        self,
        portal_url: str = URL,
        headless: bool = True,
        portal2_adapter: object | None = None,
    ) -> None:
        self._portal_url = portal_url
        self._headless = headless
        self._portal2 = portal2_adapter

    def procesar_portal_1(
        self, cedula: str, fecha_atencion: date
    ) -> tuple[str, str, str, bytes | None]:
        fecha_str = fecha_atencion.strftime("%d-%m-%Y")
        texto, pdf_bytes = scrape_cobertura(
            self._portal_url, cedula, fecha_str, headless=self._headless
        )

        # 1. Parsear RSC (formato estructurado: Institucion : ...)
        entidad_rsc, tipo_rsc, registro_rsc = self._parsear_texto_cobertura(texto)
        print(f"[DEBUG] RSC parseado: entidad='{entidad_rsc}', registro='{registro_rsc}'")

        # 2. Parsear PDF (formato tabla: buscar "si/no registra cobertura" como texto libre)
        entidad_pdf, tipo_pdf, reg_pdf = self._parsear_pdf_cobertura(pdf_bytes)

        # 3. REGLA: si el PDF tiene "si registra cobertura" → el PDF es source of truth
        if reg_pdf and "si registra cobertura" in reg_pdf.lower():
            entidad_final = entidad_pdf or entidad_rsc
            tipo_final = tipo_pdf or tipo_rsc
            print(f"[DEBUG] PDF ganó: entidad='{entidad_final}', tipo='{tipo_final}', registro='si registra cobertura'")
            return entidad_final, tipo_final, "si registra cobertura", pdf_bytes

        # 4. Si el PDF no dice "si", usar el resultado del RSC
        print(f"[DEBUG] Usando RSC: entidad='{entidad_rsc}', registro='{registro_rsc}'")
        return entidad_rsc, tipo_rsc, registro_rsc, pdf_bytes

    def existe_autenticacion_portal_3(self) -> bool:
        return False

    def vincular_sesion_portal_3(self) -> bool:
        return False

    def extraer_acreditador_portal_2(self, paciente: Paciente) -> str | None:
        if self._portal2 is None:
            return None
        return self._portal2.extraer_acreditador(
            paciente.cedula, paciente.fecha_atencion, paciente
        )

    # ──────────────────────────────────────────
    # PARSER DEL PDF (texto libre, NO formato RSC)
    # ──────────────────────────────────────────
    @staticmethod
    def _parsear_pdf_cobertura(pdf_bytes: bytes | None) -> tuple[str, str, str]:
        if pdf_bytes is None:
            return "", "", ""

        try:
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(pdf_bytes))
            texto = ""
            for page in reader.pages:
                texto += page.extract_text() or ""
        except Exception as e:
            print(f"[DEBUG] Error extrayendo texto del PDF: {e}")
            return "", "", ""

        if not texto.strip():
            print(f"[DEBUG] PDF: texto extraído vacío")
            return "", "", ""

        print(f"[DEBUG] PDF texto extraído ({len(texto)} chars):")
        print(f"[DEBUG] --- INICIO PDF ---")
        # Imprimir primeros 2000 chars para debug
        for i, linea in enumerate(texto[:2000].split("\n")):
            print(f"[DEBUG] PDF línea {i}: '{linea.strip()}'")
        print(f"[DEBUG] --- FIN PDF ---")

        lineas = texto.split("\n")
        
        # Estrategia 1: buscar "si registra cobertura" en cada línea
        for i, linea in enumerate(lineas):
            linea_lower = linea.lower().strip()
            if not linea_lower:
                continue
            
            if "si registra cobertura" in linea_lower:
                # Buscar entidad conocida en esta línea o en las cercanas
                entidad = _buscar_entidad_en_lineas(lineas, max(0, i - 3), min(len(lineas), i + 3))
                tipo = _buscar_tipo_seguro_en_lineas(lineas, max(0, i - 3), min(len(lineas), i + 3))
                print(f"[DEBUG] PDF: encontrado 'si registra cobertura' en línea {i}, entidad='{entidad}', tipo='{tipo}'")
                return entidad, tipo, "si registra cobertura"
        
        # Estrategia 2: buscar "no registra cobertura" para al menos parsear la primera fila
        for i, linea in enumerate(lineas):
            linea_lower = linea.lower().strip()
            if "no registra cobertura" in linea_lower:
                entidad = _buscar_entidad_en_lineas(lineas, max(0, i - 3), min(len(lineas), i + 3))
                tipo = _buscar_tipo_seguro_en_lineas(lineas, max(0, i - 3), min(len(lineas), i + 3))
                print(f"[DEBUG] PDF: encontrado 'no registra cobertura' en línea {i}, entidad='{entidad}'")
                return entidad, tipo, "no registra cobertura"
        
        print(f"[DEBUG] PDF: no se encontró 'registra cobertura' en el texto")
        return "", "", ""

    # ──────────────────────────────────────────
    # PARSER DEL RSC (formato estructurado)
    # ──────────────────────────────────────────
    @staticmethod
    def _parsear_texto_cobertura(texto: str) -> tuple[str, str, str]:
        entidades = re.findall(r"Institucion\s*:\s*(.+)", texto)
        tipos = re.findall(r"Tipo Seguro\s*:\s*(.+)", texto)
        coberturas = re.findall(r"Cobertura\s*:\s*(.+)", texto)
        
        if not coberturas:
            return "", "", ""
        
        # Buscar la primera fila que tenga "si registra cobertura"
        for i, cob in enumerate(coberturas):
            if "si registra cobertura" in cob.strip().lower():
                entidad = entidades[i].strip() if i < len(entidades) else ""
                tipo_seguro = tipos[i].strip() if i < len(tipos) else ""
                registro = cob.strip()
                return entidad, tipo_seguro, registro
        
        # Ninguna fila tiene "si registra cobertura" — devolver la primera
        entidad = entidades[0].strip() if entidades else ""
        tipo_seguro = tipos[0].strip() if tipos else ""
        registro = coberturas[0].strip()
        return entidad, tipo_seguro, registro


# ──────────────────────────────────────────
# FUNCIONES AUXILIARES PARA PARSING DEL PDF
# ──────────────────────────────────────────
def _buscar_entidad_en_lineas(lineas: list[str], inicio: int, fin: int) -> str:
    centro = (inicio + fin) // 2
    
    # Primero: buscar en la línea central (la que contiene el match)
    if 0 <= centro < len(lineas):
        linea = lineas[centro].upper()
        for entidad in ENTIDADES_CONOCIDAS:
            if entidad in linea:
                return entidad
    
    # Segundo: buscar en líneas anteriores (de centro hacia inicio)
    for i in range(centro - 1, inicio - 1, -1):
        if i < 0 or i >= len(lineas):
            continue
        linea = lineas[i].upper()
        for entidad in ENTIDADES_CONOCIDAS:
            if entidad in linea:
                return entidad
    
    # Tercero: buscar en líneas posteriores
    for i in range(centro + 1, fin):
        if i < 0 or i >= len(lineas):
            continue
        linea = lineas[i].upper()
        for entidad in ENTIDADES_CONOCIDAS:
            if entidad in linea:
                return entidad
    
    return ""


def _buscar_tipo_seguro_en_lineas(lineas: list[str], inicio: int, fin: int) -> str:
    for i in range(inicio, fin):
        if i < 0 or i >= len(lineas):
            continue
        linea = lineas[i].strip()
        # Buscar patrones comunes de tipo de seguro
        if any(kw in linea.lower() for kw in [
            "afiliado", "dependiente", "pensión", "beneficiario",
            "tiempo completo", "medio tiempo", "hijo", "cónyuge",
            "general", "especial", "seguro"
        ]):
            # Evitar líneas que sean solo entidad o cabecera
            if not any(e in linea.upper() for e in ENTIDADES_CONOCIDAS):
                return linea[:100]
    return ""
