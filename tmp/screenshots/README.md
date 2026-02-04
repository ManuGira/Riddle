# Grid Layout Test Screenshots

This directory contains demonstration screenshots of the CSS Grid layout with dynamic aspect-ratio, showing how the grid adapts to different container shapes.

## Screenshots

1. **grid_6x3_horizontal.png** - 6×3 grid (3 columns) in horizontal container (1400×600 viewport)
2. **grid_6x3_vertical.png** - 6×3 grid (3 columns) in vertical container (600×1400 viewport)
3. **grid_6x25_horizontal.png** - 6×25 grid (25 columns) in horizontal container (1600×600 viewport)
4. **grid_6x25_vertical.png** - 6×25 grid (25 columns) in vertical container (800×1400 viewport)

## How to Generate Screenshots

You can regenerate these screenshots using the following command:

```bash
uv run python3 << 'EOF'
from playwright.sync_api import sync_playwright
from pathlib import Path

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    
    html_path = Path('tests/playwright/test_grid_layout.html').absolute()
    
    # 6x3 horizontal (wide container)
    page.set_viewport_size({'width': 1400, 'height': 600})
    page.goto(f'file://{html_path}')
    page.evaluate('initializeGrid(6, 3)')
    page.wait_for_timeout(300)
    page.screenshot(path='tmp/screenshots/grid_6x3_horizontal.png', full_page=True)
    
    # 6x3 vertical (tall container)
    page.set_viewport_size({'width': 600, 'height': 1400})
    page.goto(f'file://{html_path}')
    page.evaluate('initializeGrid(6, 3)')
    page.wait_for_timeout(300)
    page.screenshot(path='tmp/screenshots/grid_6x3_vertical.png', full_page=True)
    
    # 6x25 horizontal (wide container)
    page.set_viewport_size({'width': 1600, 'height': 600})
    page.goto(f'file://{html_path}')
    page.evaluate('initializeGrid(6, 25)')
    page.wait_for_timeout(300)
    page.screenshot(path='tmp/screenshots/grid_6x25_horizontal.png', full_page=True)
    
    # 6x25 vertical (tall container)
    page.set_viewport_size({'width': 800, 'height': 1400})
    page.goto(f'file://{html_path}')
    page.evaluate('initializeGrid(6, 25)')
    page.wait_for_timeout(300)
    page.screenshot(path='tmp/screenshots/grid_6x25_vertical.png', full_page=True)
    
    print("Screenshots generated successfully!")
    browser.close()
EOF
```

### Prerequisites

Before running the screenshot generation:

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Install Playwright browsers:
   ```bash
   uv run playwright install chromium
   ```

### Alternative: Using a Separate Python Script

You can also create a file `generate_screenshots.py`:

```python
from playwright.sync_api import sync_playwright
from pathlib import Path

def generate_screenshots():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        
        html_path = Path('tests/playwright/test_grid_layout.html').absolute()
        
        configs = [
            ('6x3', 3, 1400, 600, 'horizontal'),
            ('6x3', 3, 600, 1400, 'vertical'),
            ('6x25', 25, 1600, 600, 'horizontal'),
            ('6x25', 25, 800, 1400, 'vertical'),
        ]
        
        for name, cols, width, height, orientation in configs:
            print(f"Generating {name} {orientation}...")
            page.set_viewport_size({'width': width, 'height': height})
            page.goto(f'file://{html_path}')
            page.evaluate(f'initializeGrid(6, {cols})')
            page.wait_for_timeout(300)
            page.screenshot(
                path=f'tmp/screenshots/grid_{name}_{orientation}.png',
                full_page=True
            )
        
        print("All screenshots generated!")
        browser.close()

if __name__ == '__main__':
    generate_screenshots()
```

Then run:
```bash
uv run python3 generate_screenshots.py
```

## Grid Configurations Demonstrated

### 6×3 Grid (Narrow)
- **Horizontal container**: Grid is width-constrained, tiles are smaller, container is wide
- **Vertical container**: Grid is height-constrained, tiles are larger, container is tall

### 6×25 Grid (Wide)
- **Horizontal container**: All 25 columns visible, tiles are very small, optimized for wide display
- **Vertical container**: Grid adapts with small tiles to fit 25 columns in narrower space

## Technical Details

The grid uses CSS Grid with dynamic aspect-ratio:
- `aspect-ratio: calc(var(--cols) / var(--rows))` - Grid maintains proper proportions
- `aspect-ratio: 1 / 1` on tiles - All tiles remain square
- CSS constraints (`max-width`, `max-height`, `min-width`, `min-height`) - Ensures grid fits container

All grids adapt automatically to their container dimensions while maintaining square tiles.
