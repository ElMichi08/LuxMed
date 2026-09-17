import json
import pytest
from pathlib import Path
from app.infrastructure.scraper.cookie_store import CookieStore


@pytest.fixture
def store(tmp_path):
    return CookieStore(path=tmp_path / "test_cookies.json")


@pytest.fixture
def sample_cookies():
    return [
        {"name": "session", "value": "abc123", "domain": ".msp.gob.ec", "path": "/"},
        {"name": "user", "value": "doctor", "domain": ".msp.gob.ec", "path": "/"},
    ]


class TestCookieStoreSave:
    def test_save_creates_file(self, store, sample_cookies):
        store.save(sample_cookies)
        assert store.path.exists()

    def test_save_valid_json(self, store, sample_cookies):
        store.save(sample_cookies)
        data = json.loads(store.path.read_text(encoding="utf-8"))
        assert "cookies" in data
        assert len(data["cookies"]) == 2

    def test_save_atomic_no_partial(self, store, sample_cookies):
        store.save(sample_cookies)
        content = store.path.read_text(encoding="utf-8")
        assert content.strip().startswith("{")


class TestCookieStoreLoad:
    def test_load_existing(self, store, sample_cookies):
        store.save(sample_cookies)
        loaded = store.load()
        assert loaded is not None
        assert len(loaded) == 2
        assert loaded[0]["name"] == "session"

    def test_load_missing_returns_none(self, store):
        assert store.load() is None

    def test_load_corrupt_deletes_and_returns_none(self, store):
        store.path.write_text("not json at all", encoding="utf-8")
        result = store.load()
        assert result is None
        assert not store.path.exists()


class TestCookieStoreDelete:
    def test_delete_existing(self, store, sample_cookies):
        store.save(sample_cookies)
        store.delete()
        assert not store.path.exists()

    def test_delete_missing_no_error(self, store):
        store.delete()


class TestCookieStoreExists:
    def test_exists_after_save(self, store, sample_cookies):
        store.save(sample_cookies)
        assert store.exists()

    def test_not_exists_initially(self, store):
        assert not store.exists()

    def test_not_exists_after_delete(self, store, sample_cookies):
        store.save(sample_cookies)
        store.delete()
        assert not store.exists()
