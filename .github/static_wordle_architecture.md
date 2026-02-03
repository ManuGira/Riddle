## Pure CSS Constraint-Based Mobile-First Layout

### Problem

The original layout used JavaScript transform scaling causing viewport overflow, broken mobile layouts, and reliance on resize calculations. Recent attempts to fix wide grid support using pure CSS faced sizing issues.

### Solution - Final Architecture

Complete CSS-only layout using dynamic aspect-ratio with proper constraint resolution:

**Critical Fix (commit 51e36ac):**
The key insight is that `max-width` and `max-height` alone don't provide an initial size - the grid needs a starting dimension. Using `width: 100%` with `height: auto` and `max-height: 100%` allows:
1. Grid starts at full container width
2. Aspect-ratio calculates height from width  
3. If calculated height exceeds available space, `max-height: 100%` constrains it
4. Aspect-ratio then reduces width proportionally to maintain square tiles

**CSS Grid with Dynamic Aspect-Ratio:**
```css
.board-grid {
    display: grid;
    grid-template-columns: repeat(var(--cols), 1fr);
    grid-template-rows: repeat(var(--rows), 1fr);
    aspect-ratio: calc(var(--cols) / var(--rows));
    
    /* Start with full width, let aspect-ratio calculate height */
    width: 100%;
    height: auto;
    max-height: 100%; /* Constrain if height exceeds available space */
}

.tile {
    aspect-ratio: 1 / 1; /* Square tiles */
    font-size: clamp(12px, 5cqmin, 32px); /* Responsive text */
}
```

**Automatic Scaling Behavior:**
- **Wide grids (6x25)**: Width fills container (100%), height calculated via aspect-ratio, all 25 columns visible with small tiles
- **Narrow grids (6x3)**: Width starts at 100%, height calculated, exceeds max-height, grid shrinks to fit height constraint, tiles expand and stay square
- **Medium grids (6x5)**: Balanced between constraints
- **Tiles always square**: CSS aspect-ratio: 1 / 1 maintains proportions
- **Text scales**: Container queries adjust font with tile size

### Architecture

**CSS-Only Layout:**
- **NO JavaScript pixel calculations**: JS only sets `--cols` and `--rows` CSS variables
- **NO resize handlers**: All responsiveness via CSS
- **NO transform scaling**: Pure CSS intrinsic sizing
- **Modern viewport units**: `100svh`/`100dvh` for mobile browser UI
- **Dynamic aspect-ratio**: `calc(var(--cols) / var(--rows))`
- **Automatic constraint selection**: CSS picks width or height limit
- **Container queries**: Responsive font sizing

**Layout Structure:**
```
.container (flex column, height: 100dvh)
├── .header-section (flex: 0 0 auto) ← intrinsic height
├── .board (flex: 1 1 auto)          ← fills remaining space  
│   └── .board-grid                  ← width: 100%, max-height: 100%
└── .keyboard (flex: 0 0 auto)       ← intrinsic height
```

### Benefits

✅ **No viewport overflow** - all grid sizes (6x3 to 6x25) stay within bounds  
✅ **No JavaScript layout logic** - pure CSS constraint-based  
✅ **Mobile browser UI compatible** - dvh units handle URL bars  
✅ **Automatic dimension selection** - CSS picks width or height constraint  
✅ **Square tiles guaranteed** - aspect-ratio: 1 / 1  
✅ **All tiles visible** - 25-column grids fully visible  
✅ **Properly centered** - Flex layout centers grid  
✅ **Responsive text** - Container queries scale fonts  
✅ **Better performance** - no JS resize calculations  
✅ **Maintainable** - declarative CSS  
✅ **Production-ready logging** - no filesystem info leakage, fail-fast on missing assets

### Technical Details

**HTML Changes:**
- `header-section` wrapper (header + game-info + message)
- Board restructured to CSS Grid (flat, not row-based)
- Tiles use `data-row`/`data-col` attributes

**CSS Changes:**
- Container: `height: 100svh; height: 100dvh;`
- Grid: `width: 100%; height: auto; max-height: 100%;`
- Aspect-ratio: `calc(var(--cols) / var(--rows))`
- Tiles: `aspect-ratio: 1 / 1;`
- Fonts: `clamp(12px, 5cqmin, 32px)`
- Flexbox: Header/keyboard `flex: 0 0 auto`, board `flex: 1 1 auto`

**JavaScript Changes:**
- Removed: tile sizing, transform scaling, resize handlers
- Added: Sets `--cols` and `--rows` CSS variables
- Simplified: Flat grid DOM structure

**Server Changes:**
- Removed noisy print statements at startup
- Fail-fast with clear exception when static directory missing
- No filesystem info leakage in production

**Migration Notes:**
- Board DOM: flexbox rows → CSS Grid
- Tile selectors: `[data-row][data-col]`
- No more `--tile-size`, `--tile-gap`, `--board-scale`
- Game logic unchanged
- Works with 3-25 letter words from server

<!-- START COPILOT CODING AGENT SUFFIX -->

