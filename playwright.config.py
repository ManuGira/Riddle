"""Playwright configuration for browser testing."""

from playwright.sync_api import sync_playwright
import pytest


# Basic pytest-playwright configuration
pytest_plugins = ["pytest_playwright"]


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for all tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
    }
