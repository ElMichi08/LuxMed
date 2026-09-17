"""Unit tests for retry_utils — exponential backoff retry wrapper."""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch, call

import pytest
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

from app.infrastructure.scraper.retry_utils import retry_with_backoff


class TestRetryWithBackoff:
    """Tests for the retry_with_backoff utility."""

    def test_success_on_first_attempt(self):
        action = MagicMock(return_value="ok")
        result = retry_with_backoff(action, max_retries=3, base_delay=5.0)
        assert result == "ok"
        assert action.call_count == 1

    def test_success_on_second_attempt(self):
        action = MagicMock(side_effect=[
            PlaywrightTimeoutError("timeout"),
            "ok",
        ])
        with patch("app.infrastructure.scraper.retry_utils.time.sleep") as mock_sleep:
            result = retry_with_backoff(action, max_retries=3, base_delay=5.0)
        assert result == "ok"
        assert action.call_count == 2
        mock_sleep.assert_called_once_with(5.0)

    def test_success_on_third_attempt(self):
        action = MagicMock(side_effect=[
            PlaywrightTimeoutError("timeout"),
            PlaywrightTimeoutError("timeout"),
            "ok",
        ])
        with patch("app.infrastructure.scraper.retry_utils.time.sleep") as mock_sleep:
            result = retry_with_backoff(action, max_retries=3, base_delay=5.0)
        assert result == "ok"
        assert action.call_count == 3
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(5.0)
        mock_sleep.assert_any_call(10.0)

    def test_exhausts_retries_raises_last_error(self):
        action = MagicMock(side_effect=PlaywrightTimeoutError("final"))
        with patch("app.infrastructure.scraper.retry_utils.time.sleep"):
            with pytest.raises(PlaywrightTimeoutError, match="final"):
                retry_with_backoff(action, max_retries=3, base_delay=5.0)
        assert action.call_count == 4  # 1 initial + 3 retries

    def test_delay_schedule_exponential(self):
        action = MagicMock(side_effect=[
            PlaywrightTimeoutError("t1"),
            PlaywrightTimeoutError("t2"),
            PlaywrightTimeoutError("t3"),
            "ok",
        ])
        with patch("app.infrastructure.scraper.retry_utils.time.sleep") as mock_sleep:
            result = retry_with_backoff(action, max_retries=3, base_delay=5.0, max_delay=20.0)
        assert result == "ok"
        delays = [c.args[0] for c in mock_sleep.call_args_list]
        assert delays == [5.0, 10.0, 20.0]

    def test_delay_capped_at_max_delay(self):
        action = MagicMock(side_effect=[
            PlaywrightTimeoutError("t1"),
            PlaywrightTimeoutError("t2"),
            PlaywrightTimeoutError("t3"),
            PlaywrightTimeoutError("t4"),
            "ok",
        ])
        with patch("app.infrastructure.scraper.retry_utils.time.sleep") as mock_sleep:
            result = retry_with_backoff(
                action, max_retries=4, base_delay=5.0, max_delay=12.0
            )
        assert result == "ok"
        delays = [c.args[0] for c in mock_sleep.call_args_list]
        # 5, 10, 12(cap), 12(cap)
        assert delays == [5.0, 10.0, 12.0, 12.0]

    def test_max_retries_zero_no_retry(self):
        action = MagicMock(side_effect=PlaywrightTimeoutError("nope"))
        with patch("app.infrastructure.scraper.retry_utils.time.sleep") as mock_sleep:
            with pytest.raises(PlaywrightTimeoutError):
                retry_with_backoff(action, max_retries=0, base_delay=5.0)
        assert action.call_count == 1
        mock_sleep.assert_not_called()

    def test_handles_playwright_error(self):
        action = MagicMock(side_effect=[
            PlaywrightError("nav destroyed"),
            "ok",
        ])
        with patch("app.infrastructure.scraper.retry_utils.time.sleep") as mock_sleep:
            result = retry_with_backoff(action, max_retries=3, base_delay=5.0)
        assert result == "ok"
        assert action.call_count == 2
        mock_sleep.assert_called_once_with(5.0)

    def test_mixed_exception_types(self):
        action = MagicMock(side_effect=[
            PlaywrightTimeoutError("timeout"),
            PlaywrightError("destroyed"),
            "ok",
        ])
        with patch("app.infrastructure.scraper.retry_utils.time.sleep") as mock_sleep:
            result = retry_with_backoff(action, max_retries=3, base_delay=5.0)
        assert result == "ok"
        assert action.call_count == 3
        assert mock_sleep.call_count == 2

    def test_non_playwright_exception_propagates_immediately(self):
        action = MagicMock(side_effect=ValueError("bad input"))
        with pytest.raises(ValueError, match="bad input"):
            retry_with_backoff(action, max_retries=3, base_delay=5.0)
        assert action.call_count == 1

    def test_custom_description_logged(self):
        action = MagicMock(side_effect=[
            PlaywrightTimeoutError("t"),
            "ok",
        ])
        with patch("app.infrastructure.scraper.retry_utils.time.sleep"):
            with patch("app.infrastructure.scraper.retry_utils.logger") as mock_log:
                retry_with_backoff(
                    action, max_retries=3, base_delay=5.0,
                    description="custom op",
                )
        mock_log.warning.assert_called_once()
        # The logger.warning call uses (fmt, *args) — check that
        # 'description' appears as one of the positional substitution args
        pos_args = mock_log.warning.call_args[0]
        assert any("custom op" == str(a) for a in pos_args)

    def test_generic_return_type(self):
        action_int = MagicMock(return_value=42)
        assert retry_with_backoff(action_int) == 42

        action_list = MagicMock(return_value=[1, 2, 3])
        assert retry_with_backoff(action_list) == [1, 2, 3]

        action_none = MagicMock(return_value=None)
        assert retry_with_backoff(action_none) is None
