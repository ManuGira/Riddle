# HTML/CSS Layout Testing - Step 4B: Fix CSS Grid Overflow with Gap and Padding

## Overview
Step 4B addresses the remaining CSS Grid overflow issue when using `gap` and `padding` properties with dynamic `aspect-ratio`. This step builds directly on Step 4's minimal reproducible bug (MRB) and will provide the final solution for the real Wordle application.

## Problem Statement

### Current Status
Step 4 successfully created a CSS Grid layout with dynamic aspect-ratio and comprehensive tests. However, the layout still violates the strict containment rules when `gap` and `padding` are applied:

**Failing Test:** `test_strict_rule_grid_must_not_overflow_board`

**Detected Violations:**
- **6×3 horizontal (1400×600)**: 15 tiles overflow board bottom by up to 343px
- **6×25 vertical (800×1400)**: 30 tiles overflow board right by up to 74px

### Root Cause
CSS Grid's `gap` property is NOT included in the grid's intrinsic size calculation when using `aspect-ratio`. The gap pixels are added on TOP of the calculated size:

```
Overflow = (n-1) × gap_size + 2 × padding
```

For example:
- 6×25 grid: (25-1) × 5px = 120px gap + 10px padding = 130px potential overflow
- 6×3 grid: (3-1) × 5px = 10px gap + 10px padding = 20px potential overflow per dimension

The aspect-ratio calculates the grid size WITHOUT accounting for these extra pixels, causing the grid to exceed its container bounds.

## Current CSS Pattern (Step 4 - With Gap/Padding Issue)

```css
.board-container {
    flex: 1 1 auto;
    width: 100%;
    min-height: 0; /* Allows flex shrinking */
    min-width: 0;
}

.board-grid {
    display: grid;
    grid-template-columns: repeat(var(--cols), 1fr);
    grid-template-rows: repeat(var(--rows), 1fr);
    gap: 5px; /* ⚠️ NOT included in aspect-ratio calculation */
    padding: 5px; /* ⚠️ Added to total size */
    
    aspect-ratio: calc(var(--cols) / var(--rows));
    width: 100%;
    height: auto;
    max-height: 100%;
    
    container-type: size;
}

.tile {
    width: 100%;
    height: 100%;
    aspect-ratio: 1 / 1;
    border: 2px solid #ccc;
}
```

## Requirements for Step 4B

### Primary Goal
Fix the CSS Grid overflow issue while maintaining `gap: 5px` and `padding: 5px` for proper visual spacing. The solution must work with ANY viewport size and grid configuration (6×3 to 6×25).

### Layout Rules (Must All Pass)
1. ✅ **Viewport constrains board** - Board never overflows viewport
2. ❌ **Board constrains grid** - Grid tiles never overflow board (CURRENTLY FAILING)
3. ✅ **Tiles are square** - aspect-ratio: 1/1 maintained
4. ✅ **Tiles scale down** - Tiles can be as small as needed to fit

### Test Requirements
All 9 tests in `tests/playwright/test_grid_layout.py` must pass:
- 6 configuration tests (already passing)
- 3 strict rule tests (1 currently failing)

## Files to Work With

### Test Files (Already Created in Step 4)
- `tests/playwright/test_grid_layout.html` - Test HTML with gap: 5px and padding: 5px restored
- `tests/playwright/test_grid_layout.py` - 9 comprehensive tests including strict rules
- `tmp/screenshots/generate_screenshots.py` - Screenshot generation script

### Documentation (To Update)
- `.github/instructions/html_css_test_step4.instructions.md` - Update with Step 4B solution
- `tmp/screenshots/README.md` - Already simplified

## Potential Approaches to Explore

### Approach 1: CSS Calc with Gap/Padding Compensation
Modify the aspect-ratio calculation to account for gap and padding:

```css
aspect-ratio: calc(
    (var(--cols) * tile-width + (var(--cols) - 1) * gap + 2 * padding) / 
    (var(--rows) * tile-height + (var(--rows) - 1) * gap + 2 * padding)
);
```

**Challenges:**
- CSS doesn't have access to tile dimensions before layout
- Circular dependency: need size to calculate size

### Approach 2: JavaScript Size Adjustment
Use JavaScript to measure and adjust grid dimensions after aspect-ratio calculation:

**Challenges:**
- Violates "pure CSS" requirement
- Adds complexity and potential race conditions

### Approach 3: CSS Container with Size Queries
Use CSS container queries to detect overflow and adjust grid size:

**Challenges:**
- Container queries measure container size, not overflow
- May not provide precise control

### Approach 4: Flexbox Wrapper for Constraint
Add a wrapper element that enforces size constraints before the grid calculates its aspect-ratio.

### Approach 5: Grid Intrinsic Sizing Override
Force the grid to calculate its size differently using `contain`, `content-visibility`, or other CSS properties.

### Approach 6: Negative Margin Technique
Use negative margins to compensate for gap and padding overflow.

## Success Criteria

### All Tests Pass
```bash
uv run pytest tests/playwright/test_grid_layout.py -v
# Expected: 9/9 tests passing
```

### Visual Verification
Regenerate screenshots and verify no overflow:
```bash
uv run python3 tmp/screenshots/generate_screenshots.py
```

All 4 screenshots should show:
- Grid fully contained within gray board-container
- 5px gap visible between tiles
- 5px padding visible around grid edges
- All tiles square and properly sized

### Works with Any Viewport
The solution must work without specifying particular viewport sizes. Test with various configurations:
- 6×3 narrow grid in horizontal/vertical containers
- 6×5 standard Wordle grid
- 6×25 wide grid in horizontal/vertical containers

## Constraints and Requirements

### Must Maintain
- ✅ Pure CSS layout (JavaScript only sets `--cols` and `--rows` variables)
- ✅ `gap: 5px` for visual spacing
- ✅ `padding: 5px` around grid
- ✅ Dynamic aspect-ratio: `calc(var(--cols) / var(--rows))`
- ✅ Square tiles: `aspect-ratio: 1/1`
- ✅ Responsive to container size
- ✅ Container queries for font sizing

### Cannot Use
- ❌ JavaScript pixel calculations or resize handlers
- ❌ Transform scaling (causes viewport overflow)
- ❌ Fixed viewport sizes (must work with any size)
- ❌ Removing gap or padding (defeats the purpose)

## Testing Strategy

### 1. Start with Failing Test
The strict rule test already fails - use it to validate your fix:
```bash
uv run pytest tests/playwright/test_grid_layout.py::test_strict_rule_grid_must_not_overflow_board -v
```

### 2. Iterative Testing
After each CSS change:
1. Run the specific failing test
2. Check if overflow is reduced
3. Verify other tests still pass
4. Generate screenshots to visually verify

### 3. Edge Cases
Test particularly challenging configurations:
- 6×3 horizontal (1400×600) - Previously 343px overflow
- 6×25 vertical (800×1400) - Previously 74px overflow
- 6×25 horizontal (1600×600) - Many small tiles
- 6×3 vertical (600×1400) - Large tiles

## Documentation Requirements

### Update Step 4 Instructions
After finding the solution, update `.github/instructions/html_css_test_step4.instructions.md`:
- Document the final working CSS pattern
- Explain why it works
- Update "Known Limitations" section
- Mark all tests as passing

### Update PR Description
Include in final commit:
- Root cause explanation
- Solution description
- Before/after screenshots
- Test results showing 9/9 passing

## References

### Step 4 Work (Completed)
- Created minimal reproducible bug (MRB)
- Added 9 comprehensive tests (6 passing, 3 strict rules with 1 failing)
- Documented CSS Grid + aspect-ratio sizing behavior
- Proved gap/padding cause overflow

### Step 4 Key Learnings
1. CSS Grid gap is NOT included in intrinsic size with aspect-ratio
2. Aspect-ratio on grid calculates size based on content, then gap is added
3. Setting gap: 0 makes tests pass (but removes visual spacing)
4. The real Wordle has this same issue - your solution will fix it

### Architecture Documentation
- `.github/instructions/static_wordle_architecture.instructions.md` - Real Wordle layout patterns
- `.github/instructions/html_css_test_step1.instructions.md` - Playwright setup
- `.github/instructions/html_css_test_step2.instructions.md` - Box model testing
- `.github/instructions/html_css_test_step3.instructions.md` - Flexbox testing
- `.github/instructions/html_css_test_step4.instructions.md` - CSS Grid testing (current state)

## Expected Timeline

- **Research and exploration**: 30-60 minutes
- **Implementation attempts**: 1-2 hours
- **Testing and validation**: 30 minutes
- **Documentation**: 30 minutes
- **Total**: 2.5-4 hours

## Deliverables

1. **Working CSS solution** in `tests/playwright/test_grid_layout.html`
2. **All 9 tests passing** (verify with pytest)
3. **Updated screenshots** showing proper containment with gap/padding
4. **Updated documentation** explaining the solution
5. **Commit message** describing the fix and why it works

## Tips for Success

1. **Study the test failure closely** - The overflow measurements tell you exactly how much extra space is being added
2. **Think about CSS sizing contexts** - Grid has multiple sizing modes (intrinsic, extrinsic, etc.)
3. **Consider the flex container** - The board-container is a flex item, which has specific sizing rules
4. **Test incrementally** - Small changes, frequent testing
5. **Use browser DevTools** - Inspect computed styles and layout to understand what's happening
6. **Read CSS specs** - CSS Grid, aspect-ratio, and flexbox specs may have relevant details
7. **Look for similar problems** - Others may have solved CSS Grid + gap + aspect-ratio issues

## Good Luck!

This is a challenging CSS problem that will provide real value to the Wordle application. The solution you find will be applied to fix the production code. Take your time, experiment with different approaches, and don't hesitate to try unconventional solutions.

The key is understanding WHY the overflow happens and finding a CSS mechanism that correctly accounts for gap and padding in the aspect-ratio-based size calculation.
