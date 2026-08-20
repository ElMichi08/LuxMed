"""Tests de frontera arquitectónica: aseguran el cumplimiento de la regla de dependencias.

Reglas hexagonales verificadas:
1. domain/ es 100% puro: no importa application, infrastructure, interface, ni librerías de I/O / externas.
2. application/ solo conoce domain y puertos propios: no importa infrastructure, interface, ni librerías concretas.
"""

import ast
from pathlib import Path

# Raíz del repositorio calculada a partir de la ubicación de este archivo de test
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOMAIN_DIR = REPO_ROOT / "domain"
APPLICATION_DIR = REPO_ROOT / "application"

# Módulos y paquetes prohibidos para el dominio (debe ser puro y sin I/O)
MODULOS_PROHIBIDOS_DOMAIN = {
    "application",
    "infrastructure",
    "interface",
    "playwright",
    "pandas",
    "openpyxl",
    "pikepdf",
    "pdfplumber",
    "sqlite3",
    "httpx",
    "pytest",
}

# Módulos y paquetes prohibidos para application (no debe depender de infra concreta ni GUI)
MODULOS_PROHIBIDOS_APPLICATION = {
    "infrastructure",
    "interface",
    "playwright",
    "pandas",
    "openpyxl",
    "pikepdf",
    "pdfplumber",
    "sqlite3",
    "httpx",
    "pytest",
}


def _verificar_archivos_sin_imports_prohibidos(
    directorio: Path, prohibidos: set[str], nombre_capa: str
) -> None:
    archivos = list(directorio.rglob("*.py"))
    assert len(archivos) > 0, f"No se encontraron archivos en {nombre_capa}/"

    violaciones: list[str] = []

    for py_file in archivos:
        codigo = py_file.read_text(encoding="utf-8")
        arbol = ast.parse(codigo, filename=str(py_file))

        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Import):
                for alias in nodo.names:
                    pkg_raiz = alias.name.split(".")[0]
                    if pkg_raiz in prohibidos:
                        rel_path = py_file.relative_to(REPO_ROOT)
                        violaciones.append(
                            f"{rel_path}:{nodo.lineno} importa módulo prohibido '{alias.name}'"
                        )
            elif isinstance(nodo, ast.ImportFrom):
                if nodo.module:
                    pkg_raiz = nodo.module.split(".")[0]
                    if pkg_raiz in prohibidos:
                        rel_path = py_file.relative_to(REPO_ROOT)
                        violaciones.append(
                            f"{rel_path}:{nodo.lineno} importa desde módulo prohibido '{nodo.module}'"
                        )

    assert not violaciones, (
        f"Se detectaron violaciones a la arquitectura hexagonal en {nombre_capa}/:\n"
        + "\n".join(f"  - {v}" for v in violaciones)
    )


def test_domain_no_importa_capas_externas_ni_librerias_prohibidas() -> None:
    _verificar_archivos_sin_imports_prohibidos(
        DOMAIN_DIR, MODULOS_PROHIBIDOS_DOMAIN, "domain"
    )


def test_application_no_importa_infrastructure_ni_interface_ni_librerias_concretas() -> (
    None
):
    _verificar_archivos_sin_imports_prohibidos(
        APPLICATION_DIR, MODULOS_PROHIBIDOS_APPLICATION, "application"
    )
