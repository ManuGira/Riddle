#!/usr/bin/env python3
"""
Generate demonstration screenshots for CSS Grid layout tests.

This script creates 4 screenshots showing how the grid adapts to different
container shapes (horizontal and vertical rectangles) with different column
configurations (6x3 narrow and 6x25 wide).

Usage:
    uv run python3 tmp/screenshots/generate_screenshots.py

Prerequisites:
    - uv sync (install dependencies)
    - uv run playwright install chromium
"""

from playwright.sync_api import sync_playwright
from pathlib import Path


def generate_screenshots():
    """Generate all 4 demonstration screenshots."""
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        # Get absolute path to test HTML file
        html_path = Path('tests/playwright/test_grid_layout.html').absolute()
        
        # Configuration: (name, cols, width, height, orientation)
        configs = [
            ('6x3', 3, 1400, 600, 'horizontal'),
            ('6x3', 3, 600, 1400, 'vertical'),
            ('6x25', 25, 1600, 600, 'horizontal'),
            ('6x25', 25, 800, 1400, 'vertical'),
        ]
        
        print("Generating CSS Grid layout screenshots...")
        print(f"HTML file: {html_path}")
        print()
        
        for name, cols, width, height, orientation in configs:
            output_file = f'tmp/screenshots/grid_{name}_{orientation}.png'
            print(f"Generating {name} {orientation} ({width}×{height})...")
            
            # Set viewport size
            page.set_viewport_size({'width': width, 'height': height})
            
            # Load HTML page
            page.goto(f'file://{html_path}')
            
            # Initialize grid with specified column count
            page.evaluate(f'initializeGrid(6, {cols})')
            
            # Wait for layout to stabilize
            page.wait_for_timeout(300)
            
            # Take screenshot
            page.screenshot(path=output_file, full_page=True)
            
            print(f"  ✓ Saved to {output_file}")
        
        print()
        print("All screenshots generated successfully!")
        browser.close()


if __name__ == '__main__':
    generate_screenshots()
