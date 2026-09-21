from __future__ import annotations

import ast
from collections.abc import Callable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
APP_DIR = REPO_ROOT / "app"
INFRASTRUCTURE_DIR = APP_DIR / "infrastructure"

EXTERNAL_LIBRARIES = frozenset(
    {"playwright", "pandas", "openpyxl", "pypdf", "sqlite3", "PyQt6", "httpx"}
)
ADAPTER_PACKAGES = ("database", "excel", "pdf", "scraper", "ui")

Rule = Callable[[Path, str], str | None]


def module_name(path: Path) -> str:
    parts = list(path.relative_to(REPO_ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def containing_package(path: Path) -> list[str]:
    parts = module_name(path).split(".")
    return parts if path.name == "__init__.py" else parts[:-1]


def imported_modules(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    package = containing_package(path)
    modules: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend((node.lineno, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                if node.module:
                    modules.append((node.lineno, node.module))
                continue
            base = package[: len(package) - (node.level - 1)]
            if node.module:
                modules.append((node.lineno, ".".join([*base, node.module])))
            else:
                modules.extend(
                    (node.lineno, ".".join([*base, alias.name])) for alias in node.names
                )
    return modules


def python_files(directory: Path) -> list[Path]:
    return sorted(directory.rglob("*.py"))


def collect_violations(files: list[Path], rule: Rule) -> list[str]:
    found: list[str] = []
    for path in files:
        for line, module in imported_modules(path):
            reason = rule(path, module)
            if reason:
                location = path.relative_to(REPO_ROOT).as_posix()
                found.append(f"{location}:{line} {reason} ('{module}')")
    return found


def assert_no_violations(files: list[Path], rule: Rule, layer: str) -> None:
    assert files, f"No se encontraron archivos en {layer}"
    found = collect_violations(files, rule)
    assert not found, f"Violaciones de dependencia en {layer}:\n" + "\n".join(
        f"  - {violation}" for violation in found
    )


def is_external(module: str) -> bool:
    return module.split(".")[0] in EXTERNAL_LIBRARIES


def domain_rule(_path: Path, module: str) -> str | None:
    if module.startswith(("app.application", "app.infrastructure")):
        return "domain no puede importar capas externas"
    if is_external(module):
        return "domain no puede importar librerias de I/O"
    return None


def application_rule(_path: Path, module: str) -> str | None:
    if module.startswith("app.infrastructure"):
        return "application no puede importar infrastructure"
    if is_external(module):
        return "application no puede importar librerias de I/O"
    return None


def adapter_rule(path: Path, module: str) -> str | None:
    own_package = path.relative_to(INFRASTRUCTURE_DIR).parts[0]
    for other in ADAPTER_PACKAGES:
        if other != own_package and module.startswith(f"app.infrastructure.{other}"):
            return (
                f"el adaptador '{own_package}' no puede importar al adaptador '{other}'"
            )
    return None


def pyqt_rule(_path: Path, module: str) -> str | None:
    if module.split(".")[0] == "PyQt6":
        return "PyQt6 solo se permite en app/infrastructure/ui"
    return None


def playwright_rule(_path: Path, module: str) -> str | None:
    if module.split(".")[0] == "playwright":
        return "playwright solo se permite en app/infrastructure/scraper"
    return None


def test_domain_es_puro() -> None:
    assert_no_violations(python_files(APP_DIR / "domain"), domain_rule, "app/domain")


def test_application_solo_depende_de_domain() -> None:
    assert_no_violations(
        python_files(APP_DIR / "application"), application_rule, "app/application"
    )


def test_adaptadores_no_se_importan_entre_si() -> None:
    files = [
        path
        for package in ADAPTER_PACKAGES
        for path in python_files(INFRASTRUCTURE_DIR / package)
    ]
    assert_no_violations(files, adapter_rule, "app/infrastructure")


def test_pyqt6_solo_en_la_interfaz() -> None:
    files = [
        path
        for path in python_files(APP_DIR)
        if INFRASTRUCTURE_DIR / "ui" not in path.parents
    ]
    assert_no_violations(files, pyqt_rule, "app (fuera de infrastructure/ui)")


def test_playwright_solo_en_scraper() -> None:
    files = [
        path
        for path in python_files(APP_DIR)
        if INFRASTRUCTURE_DIR / "scraper" not in path.parents
    ]
    assert_no_violations(
        files, playwright_rule, "app (fuera de infrastructure/scraper)"
    )
