"""
Pytest Configuration File

This file is used to define shared fixtures and test configuration.
"""

import pytest


# Configure pytest-asyncio default mode
pytest_plugins = ["pytest_asyncio"]


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
