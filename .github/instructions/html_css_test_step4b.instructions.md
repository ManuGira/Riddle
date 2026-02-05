# Step 4B: Fix CSS Grid Overflow with Gap and Padding

## Problem
CSS Grid with `gap: 5px` and `padding: 5px` causes tile overflow when using dynamic `aspect-ratio`. The grid exceeds its board-container boundaries.

**Failing Test:** `test_strict_rule_grid_must_not_overflow_board` (8/9 tests passing)

**Overflow Amounts:**
- 6×3 horizontal (1400×600): 343px bottom overflow
- 6×25 vertical (800×1400): 74px right overflow

## Root Cause
CSS Grid gap is NOT included in intrinsic size calculation with `aspect-ratio`. The gap and padding pixels are added ON TOP of the calculated size.

**Critical Discovery:** Setting `gap: 0px` and `padding: 0px` does NOT fix overflow, indicating a deeper CSS Grid + aspect-ratio sizing issue.

**Key Insight:** The `gap: 5px` uses fixed pixels that don't scale. Gap should be proportional to tile size (10-20× smaller than tiles), not absolute pixels.

## Current CSS (Has Overflow)
```css
.board-container {
    flex: 1 1 auto;
    width: 100%;
    min-height: 0;
}

.board-grid {
    display: grid;
    grid-template-columns: repeat(var(--cols), 1fr);
    grid-template-rows: repeat(var(--rows), 1fr);
    gap: 5px;           /* ⚠️ Causes overflow */
    padding: 5px;       /* ⚠️ Causes overflow */
    aspect-ratio: calc(var(--cols) / var(--rows));
    width: 100%;
    height: auto;
    max-height: 100%;
}

.tile {
    width: 100%;
    height: 100%;
    aspect-ratio: 1 / 1;
}
```

## Goal
Fix overflow while maintaining visual spacing. Solution must work with ANY viewport size and grid configuration (6×3 to 6×25).

## Layout Rules (All Must Pass)
1. ✅ Viewport constrains board
2. ❌ **Board constrains grid** (FAILING - fix this)
3. ✅ Tiles are square
4. ✅ Tiles scale down as needed

## Files
- `tests/playwright/test_grid_layout.html` - CSS to fix
- `tests/playwright/test_grid_layout.py` - 9 tests (run all)
- `tmp/screenshots/generate_screenshots.py` - Visual verification

## Approaches to Try
1. **Relative gap units** - Use % or calc() instead of fixed 5px
2. **Wrapper element** - Add constraint layer before grid calculates size
3. **CSS contain property** - Force different sizing behavior
4. **Negative margins** - Compensate for gap/padding overflow
5. **Grid intrinsic sizing** - Modify how grid calculates its size

## Testing
```bash
# Run failing test
uv run pytest tests/playwright/test_grid_layout.py::test_strict_rule_grid_must_not_overflow_board -v

# Run all tests
uv run pytest tests/playwright/test_grid_layout.py -v

# Generate screenshots (after fix)
uv run python3 tmp/screenshots/generate_screenshots.py
```

## Success Criteria
- All 9 tests passing
- Screenshots show grid within gray border
- Gap and padding visible (5px each)
- Works with any viewport size

## Constraints
**Must keep:** Pure CSS, gap: 5px, padding: 5px, dynamic aspect-ratio, square tiles  
**Cannot use:** JavaScript sizing, transform scaling, fixed viewports, removing gap/padding
