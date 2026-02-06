# Grid Layout Test Screenshots

Demonstration screenshots showing CSS Grid layout with dynamic aspect-ratio adapting to different container shapes.

## Screenshots

1. **grid_6x3_horizontal.png** - 6×3 grid (3 columns) in horizontal container (1400×600)
2. **grid_6x3_vertical.png** - 6×3 grid (3 columns) in vertical container (600×1400)
3. **grid_6x25_horizontal.png** - 6×25 grid (25 columns) in horizontal container (1600×600)
4. **grid_6x25_vertical.png** - 6×25 grid (25 columns) in vertical container (800×1400)

## How to Regenerate

Run the generation script:

```bash
uv run python3 tmp/screenshots/generate_screenshots.py
```

### Prerequisites

1. Install dependencies:
   ```bash
   uv sync
   ```

2. Install Playwright browsers:
   ```bash
   uv run playwright install chromium
   ```

## What the Screenshots Demonstrate

### 6×3 Grid (Narrow)
- **Horizontal container**: Width-constrained, smaller tiles, wide container
- **Vertical container**: Height-constrained, larger tiles, tall container

### 6×25 Grid (Wide)
- **Horizontal container**: All 25 columns visible, very small tiles
- **Vertical container**: 25 columns adapted to narrower space

## Technical Details

The grid uses:
- `aspect-ratio: calc(var(--cols) / var(--rows))` - Grid maintains proportions
- `aspect-ratio: 1 / 1` on tiles - All tiles remain square
- CSS constraints - Grid adapts to container size
- No JavaScript sizing - Only configuration via CSS variables
