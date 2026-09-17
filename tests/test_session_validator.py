from unittest.mock import MagicMock, patch
import pytest
from app.infrastructure.scraper.session_validator import SessionValidator
from app.infrastructure.scraper.cookie_store import CookieStore


@pytest.fixture
def store(tmp_path):
    s = CookieStore(path=tmp_path / "test_cookies.json")
    return s


@pytest.fixture
def validator(store):
    return SessionValidator(cookie_store=store, validation_url="https://test.example.com/protected")


class TestSessionValidator:
    def test_no_cookies_returns_false(self, validator):
        assert validator.is_valid() is False

    @patch("app.infrastructure.scraper.session_validator.sync_playwright")
    def test_valid_cookies_returns_true(self, mock_pw, store):
        store.save([{"name": "sid", "value": "abc", "domain": ".example.com", "path": "/"}])
        mock_page = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_page.goto.return_value = mock_response
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context
        mock_pw.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser

        validator = SessionValidator(cookie_store=store)
        assert validator.is_valid() is True

    @patch("app.infrastructure.scraper.session_validator.sync_playwright")
    def test_expired_cookies_returns_false(self, mock_pw, store):
        store.save([{"name": "sid", "value": "expired", "domain": ".example.com", "path": "/"}])
        mock_page = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 401
        mock_page.goto.return_value = mock_response
        mock_context = MagicMock()
        mock_context.new_page.return_value = mock_page
        mock_browser = MagicMock()
        mock_browser.new_context.return_value = mock_context
        mock_pw.return_value.__enter__.return_value.chromium.launch.return_value = mock_browser

        validator = SessionValidator(cookie_store=store)
        assert validator.is_valid() is False
        assert not store.path.exists()
