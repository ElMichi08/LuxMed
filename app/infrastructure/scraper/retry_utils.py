from __future__ import annotations
import logging
import time
from typing import Callable, TypeVar
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    action: Callable[[], T],
    max_retries: int = 3,
    base_delay: float = 5.0,
    max_delay: float = 20.0,
    description: str = "operation",
) -> T:
    """Execute action with exponential backoff on Playwright errors.

    Handles both TimeoutError and general Playwright Error (e.g., navigation context destroyed).
    Delay schedule: 5s, 10s, 20s (capped). Total max ~35s for retries
    plus action execution time. Raises the last error after max_retries exhausted.
    """
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return action()
        except (PlaywrightTimeoutError, PlaywrightError) as e:
            last_error = e
            if attempt < max_retries:
                delay = min(base_delay * (2 ** attempt), max_delay)
                logger.warning(
                    "Retry %d/%d for %s after %.1fs backoff: %s",
                    attempt + 1, max_retries, description, delay, e,
                )
                time.sleep(delay)
    raise last_error  # type: ignore[misc]
