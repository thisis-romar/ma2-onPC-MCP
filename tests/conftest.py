"""
Pytest Configuration File

This file is used to define shared fixtures and test configuration.
"""

import asyncio

import pytest

# Configure pytest-asyncio default mode
pytest_plugins = ["pytest_asyncio"]

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


@pytest.fixture
def mock_gma_host():
    """Provide test grandMA2 host IP."""
    return "127.0.0.1"


@pytest.fixture
def mock_gma_port():
    """Provide test grandMA2 port."""
    return 30000


@pytest.fixture
def mock_gma_credentials():
    """Provide test grandMA2 login credentials."""
    return {"user": "administrator", "password": "admin"}
