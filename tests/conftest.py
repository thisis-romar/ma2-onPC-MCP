"""
Pytest Configuration File

This file is used to define shared fixtures and test configuration.
"""

import asyncio
import os

import pytest

# Configure pytest-asyncio default mode
pytest_plugins = ["pytest_asyncio"]


# ---------------------------------------------------------------------------
# OAuth scope bypass — enable for all unit/integration tests
# ---------------------------------------------------------------------------
# All non-live unit tests run with GMA_AUTH_BYPASS=1 so that @require_scope
# decorators are transparent. Auth-specific tests that need to exercise scope
# checking call ``monkeypatch.delenv("GMA_AUTH_BYPASS", raising=False)``
# explicitly to opt out of bypass mode for that individual test.


@pytest.fixture(autouse=True)
def _auth_bypass(monkeypatch):
    """Set GMA_AUTH_BYPASS=1 for every test unless it opts out via monkeypatch."""
    monkeypatch.setenv("GMA_AUTH_BYPASS", "1")

# ---------------------------------------------------------------------------
# Live-test pacing — prevent overwhelming grandMA2 onPC with rapid commands
# ---------------------------------------------------------------------------
# grandMA2 onPC can freeze/hang when receiving commands faster than it can
# process them. This autouse fixture adds a mandatory cooldown after every
# live test to give the console time to settle.

LIVE_TEST_COOLDOWN = 1.0  # seconds between tests — onPC needs time to process


@pytest.fixture(autouse=True)
async def _live_test_pacing(request):
    """Add cooldown after every ``@pytest.mark.live`` test."""
    yield
    if request.node.get_closest_marker("live"):
        await asyncio.sleep(LIVE_TEST_COOLDOWN)


def pytest_addoption(parser):
    """Add custom CLI options."""
    parser.addoption(
        "--destructive",
        action="store_true",
        default=False,
        help="Enable destructive live tests that modify show data",
    )


def pytest_collection_modifyitems(config, items):
    """Skip destructive tests unless --destructive is passed."""
    if not config.getoption("--destructive"):
        skip_destructive = pytest.mark.skip(
            reason="Destructive tests require --destructive flag"
        )
        for item in items:
            if "destructive" in item.keywords:
                item.add_marker(skip_destructive)
