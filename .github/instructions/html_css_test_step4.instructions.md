# HTML/CSS Layout Testing - Step 4: CSS Grid with Dynamic Aspect-Ratio

## Overview
Step 4 validates CSS Grid layout with dynamic aspect-ratio for rendering square tile grids at various dimensions (6×3 to 6×25 columns). This is a direct precursor to testing the real Wordle board in Step 5.

## Files Created
- `tests/playwright/test_grid_layout.html` - Test HTML with CSS Grid
- `tests/playwright/test_grid_layout.py` - 9 comprehensive tests
- `tmp/screenshots/generate_screenshots.py` - Screenshot generation script
- `tmp/screenshots/*.png` - 4 demonstration screenshots

## Core CSS Pattern

```css
.board-grid {
    display: grid;
    grid-template-columns: repeat(var(--cols), 1fr);
    grid-template-rows: repeat(var(--rows), 1fr);
    aspect-ratio: calc(var(--cols) / var(--rows));
    width: 100%;
    height: auto;
    max-width: 100%;
    max-height: 100%;
    min-width: 0;
    min-height: 0;
    container-type: size;
}

.tile {
    aspect-ratio: 1 / 1; /* Square tiles */
}
```

**JavaScript (configuration only):**
```javascript
document.documentElement.style.setProperty('--cols', cols);
document.documentElement.style.setProperty('--rows', rows);
```

## Test Suite (9 Tests)

### Basic Configuration Tests (6 tests)
1. **test_grid_6x3_narrow_configuration** - Height-constrained narrow grid
2. **test_grid_6x5_balanced_configuration** - Standard Wordle dimensions  
3. **test_grid_6x25_wide_configuration** - Width-constrained wide grid (all 25 columns visible)
4. **test_grid_configuration_switching** - Dynamic switching between configurations
5. **test_grid_css_variables** - CSS variable usage validation
6. **test_grid_tiles_do_not_overflow_container** - Overflow stays under control

### Strict Rule Validation Tests (3 tests - all passing after fix)
7. **test_strict_rule_board_must_not_overflow_viewport** ✅ PASSES
8. **test_strict_rule_grid_must_not_overflow_board** ✅ PASSES (fixed)
9. **test_strict_rule_tiles_must_be_square** ✅ PASSES

**Current Status:** All 9 tests passing (grid overflow fixed)

**Previous violations (now fixed):**
- 6×3 horizontal (1400×600): 15 tiles were overflowing board bottom by up to 343px → **FIXED**
- 6×25 vertical (800×1400): 30 tiles were overflowing board right by up to 74px → **FIXED**

## Layout Rules to Enforce

1. **Viewport → Board**: Board must stay within viewport (✅ passing)
2. **Board → Grid**: Grid tiles must stay within board (✅ passing - fixed)
3. **Tiles**: Must be square (✅ passing)
4. **Tiles**: Can be as small as needed to fit (✅ passing)

## Key Learnings

### What Works Reliably ✅
1. **Dynamic Aspect-Ratio**: Grid proportions adapt automatically via `calc(var(--cols) / var(--rows))`
2. **Square Tiles**: `aspect-ratio: 1 / 1` guarantees square shape at any size
3. **CSS Variables**: Configuration changes trigger automatic relayout
4. **Wide Grid Support**: All 25 columns visible with small square tiles
5. **No JavaScript Sizing**: Only sets semantic configuration

### What Requires Understanding ⚠️
1. **CSS Grid Measurements**: Bounding box may not perfectly match visual containment due to aspect-ratio + grid track calculations
2. **Overflow Behavior**: Current implementation has measured overflow that needs CSS fix
3. **Container Queries**: `container-type: size` required for Step 5 responsive font sizing
4. **Viewport Units**: Step 5 will use dvh for mobile browser UI

### Issue Resolution ✅
**Problem:** CSS Grid with aspect-ratio tiles was overflowing the board container in certain configurations (6×3 horizontal: 343px overflow, 6×25 vertical: 74px overflow).

**Root Cause:** Extra CSS constraints (`max-width`, `min-width`, `min-height` on grid, `min-width` on board-container) were interfering with aspect-ratio's automatic constraint resolution mechanism.

**Solution:** Simplified CSS to match real Wordle pattern exactly:
- Board: `width: 100%; min-height: 0;` (removed `min-width: 0`)
- Grid: `width: 100%; height: auto; max-height: 100%;` (removed `max-width`, `min-width`, `min-height`)

**How it works:** Aspect-ratio automatically selects the limiting dimension - wide grids are width-constrained, narrow grids are height-constrained, tiles stay square.

## Testing Approach

**Reliable Assertions:**
```python
# Tile squareness (1px tolerance for rounding)
assert abs(tile_bbox["width"] - tile_bbox["height"]) <= 1

# Tile visibility
assert tile.is_visible()

# Strict containment (board in viewport, grid in board)
assert board_bbox["x"] >= 0
assert board_bbox["y"] >= 0
assert tile_bbox["right"] <= board_bbox["right"]
assert tile_bbox["bottom"] <= board_bbox["bottom"]
```

**Test Commands:**
```bash
# Run all grid tests
uv run pytest tests/playwright/test_grid_layout.py -v

# Run specific test
uv run pytest tests/playwright/test_grid_layout.py::test_strict_rule_grid_must_not_overflow_board -v

# Generate screenshots
uv run python3 tmp/screenshots/generate_screenshots.py
```

## Patterns for Step 5

### ✅ Reuse These Patterns
1. CSS Grid with `repeat(var(--cols), 1fr)` for dynamic tracks
2. Dynamic `aspect-ratio: calc(var(--cols) / var(--rows))` on grid
3. Tile `aspect-ratio: 1 / 1` for square shape
4. CSS variables on `:root` for configuration
5. `container-type: size` for responsive font sizing
6. Test assertions: tile squareness, visibility, containment

### 🎯 Step 5 Testing Goals
1. Test real Wordle board from `src/static/`
2. Validate word lengths 3, 5, 10, 25
3. Test tile states (correct, present, absent, empty)
4. Validate container queries for responsive fonts (cqmin units)
5. Test multiple viewports (mobile/tablet/desktop)
6. Test dvh units for mobile browser UI

### ⚠️ Known Limitations
1. **None remaining** - Grid overflow issue has been fixed
2. **CSS Grid Quirks**: Bounding box measurements with aspect-ratio tiles are complex - tests validate correctness
3. **Small Tiles**: 6×25 grid creates ~30px tiles - usable but requires adequate viewport (1280px+ width recommended)

## Design Decisions

1. **CSS Variables on :root**: Matches real Wordle, allows variables anywhere
2. **Container Queries**: Required for Step 5 responsive font sizing
3. **Flexbox for Centering**: Matches Wordle architecture, provides definite height
4. **Flat Grid Structure**: All tiles direct children of grid (no row wrappers)
5. **Deterministic Viewports**: 800×600 (narrow), 1280×720 (wide), custom sizes for demos

## TDD Approach Followed

1. ✅ Created basic tests validating CSS Grid works (6 tests)
2. ✅ Added strict rule tests BEFORE implementing fix (3 tests)
3. ✅ Confirmed tests can detect violations (1 test failing as expected)
4. ✅ **Implemented CSS fix** - Simplified to match real Wordle pattern
5. ✅ **All tests passing** - Grid overflow resolved

## Screenshot Generation

Run the script to generate all 4 demonstration screenshots:
```bash
uv run python3 tmp/screenshots/generate_screenshots.py
```

Screenshots demonstrate:
- **6×3 horizontal/vertical**: Narrow grid adapting to different containers
- **6×25 horizontal/vertical**: Wide grid with all 25 columns visible

## Resources
- [CSS Grid Layout](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Grid_Layout)
- [aspect-ratio](https://developer.mozilla.org/en-US/docs/Web/CSS/aspect-ratio)
- [Container Queries](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Container_Queries)
- [Wordle Layout Architecture](.github/instructions/static_wordle_architecture.instructions.md)
- [Steps 1-3 Instructions](./html_css_test_step1.instructions.md)
