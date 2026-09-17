from __future__ import annotations
import json
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_COOKIE_PATH = Path("data/cookies_portal3.json")


class CookieStore:
    def __init__(self, path: Path | str = DEFAULT_COOKIE_PATH) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    def exists(self) -> bool:
        return self._path.exists() and self._path.stat().st_size > 0

    def save(self, cookies: list[dict]) -> None:
        tmp_fd, tmp_path = tempfile.mkstemp(
            dir=str(self._path.parent), suffix=".tmp"
        )
        try:
            with open(tmp_fd, "w", encoding="utf-8") as f:
                json.dump({"cookies": cookies}, f, ensure_ascii=False, indent=2)
            Path(tmp_path).replace(self._path)
            logger.info("Cookies guardadas en %s (%d entradas)", self._path, len(cookies))
        except Exception:
            try:
                Path(tmp_path).unlink(missing_ok=True)
            except Exception:
                pass
            raise

    def load(self) -> list[dict] | None:
        if not self.exists():
            return None
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cookies = data.get("cookies", [])
            if not isinstance(cookies, list):
                raise ValueError("Formato de cookies inválido: se esperaba array")
            return cookies
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning("Cookie file corrupto o inválido: %s — eliminando", e)
            self.delete()
            return None

    def delete(self) -> None:
        try:
            self._path.unlink(missing_ok=True)
            logger.info("Cookie file eliminado: %s", self._path)
        except Exception as e:
            logger.warning("No se pudo eliminar cookie file: %s", e)
