"""Smoke test for Playwright browser automation.

This is a minimal test to verify that Playwright can:
1. Launch a browser
2. Load a simple HTML page
3. Interact with page content
"""

import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def test_page_path():
    """Return the path to the test HTML page."""
    return Path(__file__).parent / "test_page.html"


def test_playwright_smoke(page, test_page_path):
    """Smoke test: Verify Playwright can launch browser and load a page.
    
    This test validates:
    - Browser launches successfully
    - Page navigation works
    - DOM element querying works
    - Text content can be read
    """
    # Navigate to the test page
    page.goto(f"file://{test_page_path}")
    
    # Verify the page loaded by checking the title
    assert page.title() == "Playwright Smoke Test"
    
    # Verify we can query and read elements
    heading = page.locator("h1")
    assert heading.text_content() == "Playwright Test Page"
    
    # Verify status element exists
    status = page.locator("#test-status")
    assert status.text_content() == "Ready for testing"
    
    # Take a screenshot to demonstrate browser is working
    # This is purely informational and won't fail the test
    try:
        page.screenshot(path="tests/playwright/smoke_test_screenshot.png")
    except Exception:
        # Screenshot failures shouldn't break the smoke test
        pass


def test_browser_basic_functionality(page):
    """Test basic browser navigation and interaction capabilities.
    
    This test validates:
    - Navigation to about:blank works
    - JavaScript evaluation works
    - Content injection works
    """
    # Navigate to a blank page
    page.goto("about:blank")
    
    # Inject some content to verify JS execution works
    page.evaluate("""
        document.body.innerHTML = '<div id="test">Playwright is working!</div>';
    """)
    
    # Verify the injected content
    test_div = page.locator("#test")
    assert test_div.text_content() == "Playwright is working!"
