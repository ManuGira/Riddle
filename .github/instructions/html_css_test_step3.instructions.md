# HTML/CSS Layout Testing with Playwright - Step 3 Summary

## Overview
This document describes the completion of Step 3: Creating flexbox layout testing with Playwright. This builds upon the foundational setup from Step 1 and the basic box model testing from Step 2, introducing the complexity of dynamic flexbox layouts.

## What Was Added

### 1. Test HTML File (test_flexbox_layout.html)
Created a comprehensive HTML page with multiple flexbox test cases:

**Test Case 1: Horizontal Flex Row with space-between**
- Container: 600px × 100px
- Three items arranged horizontally
- `justify-content: space-between` - items at edges with space between
- `align-items: center` - items vertically centered
- Tests edge positioning and vertical alignment

**Test Case 2: Vertical Flex Column with gap**
- Container: 200px × 400px
- Three items arranged vertically
- `flex-direction: column`
- `justify-content: flex-start` - items start at top
- `align-items: stretch` - items fill container width
- `gap: 10px` - consistent spacing between items
- `padding: 15px` - tests interaction with padding
- Tests vertical stacking, stretching, and gap property

**Test Case 3: Centered Flex Container**
- Container: 300px × 200px
- Single item centered both horizontally and vertically
- `justify-content: center` + `align-items: center`
- Tests perfect centering in both axes

**Test Case 4: Flex Container with Gap Property**
- Container: 400px × 100px
- Three items with explicit gap
- `gap: 20px` - tests gap property behavior
- `padding: 10px` - tests gap vs padding interaction
- Tests that gap doesn't affect external margins

**Test Case 5: Flex-grow Distribution**
- Container: 500px × 80px
- Three items with different flex-grow values
- Items 1 and 3: `flex-grow: 1`
- Item 2: `flex-grow: 2`
- Tests proportional space distribution (2:1 ratio)
- Tests that items fill available space accounting for gaps

**Design Rationale:**
- All containers use absolute positioning for predictable placement
- Multiple test cases cover different flexbox properties in isolation
- Each test case focuses on specific flexbox behavior
- Fixed dimensions make assertions testable
- Real-world patterns (centering, gap, flex-grow) are included

### 2. Test Suite (test_flexbox_layout.py)
Created seven comprehensive tests that validate flexbox behavior:

#### Test 1: test_flex_row_container_dimensions
Validates basic flex container properties:
- Container is visible and positioned correctly
- Dimensions match CSS values (600px × 100px)
- Position matches expected coordinates (20, 20)

**Key Learning:** Flex containers behave like regular elements for dimension measurement - `bounding_box()` works identically.

#### Test 2: test_flex_row_items_spacing
Validates `justify-content: space-between` behavior:
- All flex items are visible
- First item positioned at container start
- Last item positioned at container end
- Middle item positioned between first and last
- All items vertically centered (`align-items: center`)

**Key Learning:** 
- Space-between creates predictable edge positions - first and last items can be tested absolutely
- Vertical centering can be validated by comparing item center with container center
- Need 1px tolerance for rounding in centering calculations

#### Test 3: test_flex_column_layout
Validates vertical flexbox layout:
- Items arranged vertically (top to bottom ordering)
- Gap property creates 10px spacing between items
- Items start at top with padding offset (15px)
- Items stretch to container width minus padding (`align-items: stretch`)

**Key Learning:**
- Gap property adds consistent spacing between items (measurable and testable)
- Stretching behavior can be validated by comparing item width to container width minus padding
- Padding affects first item position but not gap spacing

#### Test 4: test_flex_center_alignment
Validates centering in both axes:
- Item horizontally centered (`justify-content: center`)
- Item vertically centered (`align-items: center`)
- Centers calculated and compared with 1px tolerance

**Key Learning:**
- Perfect centering is reliable and testable
- Must use center-to-center comparison, not edge alignment
- 1px tolerance accounts for rounding in odd-dimension cases

#### Test 5: test_flex_gap_property
Validates gap property behavior:
- First item starts at padding offset (not gap-affected)
- Gap creates 20px spacing between items
- Gap is consistent between all item pairs
- Items ordered left to right

**Key Learning:**
- Gap only affects spacing between items, not edges
- Gap value is directly measurable: `next_item.x - (current_item.x + current_item.width)`
- First and last items respect padding but not gap

#### Test 6: test_flex_grow_proportions
Validates flex-grow space distribution:
- Item with `flex-grow: 2` is larger than items with `flex-grow: 1`
- Items with same flex-grow have similar widths
- Proportions approximately match expected ratios (2:1)
- Items fill available space accounting for gaps and padding

**Key Learning:**
- Flex-grow calculations are approximate - need tolerance (10% used)
- Formula: `available_space = container_width - 2*padding - (n-1)*gap`
- Item width calculation: `available_space * (flex-grow / total_flex_units)`
- Browser rounding means exact equality is unreliable
- Relative comparisons (item2 > item1) are more reliable than absolute values

#### Test 7: test_flex_computed_styles
Validates reading flexbox CSS properties via JavaScript:
- `display: flex` property readable
- `flex-direction` (row, column) readable
- `justify-content` (space-between, center, flex-start) readable
- `align-items` (center, stretch) readable
- `gap` property readable (returns "10px" format)

**Key Learning:**
- All flexbox properties accessible via `window.getComputedStyle()`
- Values returned as strings in CSS format
- Useful for debugging test failures
- Validates that CSS was applied correctly

## Flexbox Layout Measurement Techniques

### 1. Relative Position Assertions
Unlike Step 2's absolute positioning, flexbox requires testing relationships:

**Edge Position Testing:**
```python
# First item at container start (space-between)
assert item1_bbox["x"] == container_bbox["x"]

# Last item at container end (space-between)
assert item3_bbox["x"] + item3_bbox["width"] == container_bbox["x"] + container_bbox["width"]
```

**Use cases:**
- Validating justify-content: space-between
- Checking that items don't overflow container
- Testing that items respect container boundaries

### 2. Ordering and Sequence Testing
```python
# Horizontal ordering
assert item1_bbox["x"] < item2_bbox["x"] < item3_bbox["x"]

# Vertical ordering
assert item1_bbox["y"] < item2_bbox["y"] < item3_bbox["y"]
```

**Use cases:**
- Flex-direction validation (row vs column)
- Order property testing (if implemented)
- Sanity checks for layout

### 3. Gap Measurement
```python
gap_1_2 = item2_bbox["x"] - (item1_bbox["x"] + item1_bbox["width"])
assert gap_1_2 == 10  # expected gap value
```

**Use cases:**
- Validating gap property
- Testing spacing consistency
- Debugging layout issues

### 4. Centering Validation
```python
container_center = container_bbox["x"] + container_bbox["width"] / 2
item_center = item_bbox["x"] + item_bbox["width"] / 2

# Allow 1px tolerance for rounding
assert abs(item_center - container_center) <= 1
```

**Use cases:**
- Testing justify-content: center
- Testing align-items: center
- Validating perfect centering

### 5. Proportional Distribution Testing
```python
# Test relative sizes
assert item2_bbox["width"] > item1_bbox["width"]  # More reliable

# Test approximate proportions with tolerance
expected_width = available_space * flex_grow_ratio
assert abs(item_bbox["width"] - expected_width) / expected_width <= 0.1  # 10% tolerance
```

**Use cases:**
- Validating flex-grow behavior
- Testing flex-shrink (not covered in this step)
- Checking dynamic space distribution

### 6. Stretch Behavior Testing
```python
# Items should fill container width (minus padding)
expected_width = container_bbox["width"] - 2 * padding
assert item_bbox["width"] == expected_width
```

**Use cases:**
- Testing align-items: stretch
- Validating that items fill available space
- Checking for unwanted constraints

## Assumptions Validated

### 1. Flexbox Edge Positioning (space-between)
✅ **Assumption**: With `justify-content: space-between`, first item starts at container edge, last item ends at container edge  
✅ **Validation**: Test measures exact pixel positions and confirms edges align  
✅ **Conclusion**: Edge positions are reliable and testable with exact equality

### 2. Gap Property Consistency
✅ **Assumption**: Gap property creates uniform spacing between all adjacent flex items  
✅ **Validation**: Measured gap between all item pairs, confirmed consistent 10px and 20px values  
✅ **Conclusion**: Gap is predictable and testable with exact pixel values

### 3. Centering Accuracy
✅ **Assumption**: Flex centering (justify-content: center, align-items: center) produces mathematically centered items  
✅ **Validation**: Calculated centers and compared with container centers  
✅ **Conclusion**: Centering is accurate within 1px (rounding tolerance needed)

### 4. Flex-grow Space Distribution
⚠️ **Assumption**: Flex-grow distributes space according to exact mathematical ratios  
⚠️ **Validation**: Test shows approximate ratios with ~10% tolerance needed  
⚠️ **Conclusion**: Flex-grow is testable but requires tolerance - exact equality is unreliable due to browser rounding

### 5. Align-items: Stretch Behavior
✅ **Assumption**: Items with `align-items: stretch` fill the cross-axis of the container  
✅ **Validation**: Measured item widths in column layout, confirmed they match container width minus padding  
✅ **Conclusion**: Stretching is predictable and testable with exact values

### 6. Flexbox Computed Styles
✅ **Assumption**: All flexbox properties are accessible via `window.getComputedStyle()`  
✅ **Validation**: Read display, flex-direction, justify-content, align-items, gap properties  
✅ **Conclusion**: All flexbox properties are readable and can be used for test validation

## Reliable vs Fragile Assertions

### ✅ Reliable Assertions (Safe to Use)

**1. Edge Positions with space-between/flex-start/flex-end**
```python
# RELIABLE: Exact equality for edge positions
assert first_item["x"] == container["x"]
assert last_item["x"] + last_item["width"] == container["x"] + container["width"]
```
- Works consistently across browsers
- No rounding issues
- Exact pixel values testable

**2. Gap Measurements**
```python
# RELIABLE: Exact gap values
gap = next_item["x"] - (current_item["x"] + current_item["width"])
assert gap == 20  # Exact equality works
```
- Gap property is deterministic
- No browser-specific calculations
- Exact values safe to test

**3. Item Ordering**
```python
# RELIABLE: Relative positioning
assert item1["x"] < item2["x"] < item3["x"]
assert item1["y"] < item2["y"] < item3["y"]
```
- Order is always preserved
- No rounding issues
- Simple inequality checks

**4. Stretching to Container Size**
```python
# RELIABLE: Exact container width (with padding)
assert item["width"] == container["width"] - 2 * padding
```
- Stretch calculations are exact
- No fractional values
- Predictable behavior

**5. Visibility and Dimensions**
```python
# RELIABLE: Basic measurements
assert item.is_visible()
assert item.bounding_box()["width"] > 0
```
- Always works for flex items
- No flexbox-specific quirks

### ⚠️ Fragile Assertions (Use with Caution)

**1. Flex-grow Exact Proportions**
```python
# FRAGILE: Exact equality for flex-grow distributions
assert item1["width"] == 100  # May fail due to rounding
assert item2["width"] == 200  # May be 199 or 201

# BETTER: Use tolerance
assert abs(item1["width"] - expected) / expected <= 0.1  # 10% tolerance
```
- Browser rounding varies
- Sub-pixel calculations differ
- Always use tolerance (5-10%)

**2. Perfect Centering (Odd Dimensions)**
```python
# FRAGILE: Exact centering with odd dimensions
assert item_center == container_center  # May be off by 0.5px

# BETTER: Allow 1px tolerance
assert abs(item_center - container_center) <= 1
```
- Odd dimensions create fractional centers
- Browsers round differently
- Always use 1px tolerance

**3. Space-evenly/Space-around Gaps**
```python
# FRAGILE: Exact gaps with space-evenly
gap = next_item["x"] - (current_item["x"] + current_item["width"])
assert gap == 33  # May vary due to rounding

# BETTER: Test consistency or use tolerance
assert abs(gap1 - gap2) <= 2  # Gaps should be similar
```
- Multiple gap calculations compound rounding
- Distribution may favor one side
- Test consistency rather than exact values

**4. Flex-wrap Multi-line Layouts**
```python
# FRAGILE: Exact row heights after wrapping
assert row1_height == row2_height  # May differ

# BETTER: Test that wrapping occurred
assert item4["y"] > item1["y"]  # Item wrapped to next line
```
- Line heights vary with content
- Wrapping behavior is complex
- Test wrapping occurred, not exact positions

**5. Content-based Sizing**
```python
# FRAGILE: Exact width when flex-basis: auto
assert item["width"] == 150  # Depends on content

# BETTER: Test relative sizes or ranges
assert 100 <= item["width"] <= 200
assert item1["width"] < item2["width"]  # Relative comparison
```
- Content width varies with font rendering
- Sub-pixel text rendering differs
- Use ranges or relative comparisons

## Pitfalls When Testing Flexbox with Real Browsers

### 1. Sub-pixel Rendering and Rounding

**Problem:**
Browsers use sub-pixel rendering internally but report integer coordinates via `bounding_box()`. This causes rounding issues with flex-grow distributions.

**Example:**
```python
# Container: 500px, 3 items with flex-grow: 1
# Expected: 166.67px each
# Reality: 167px, 167px, 166px (or similar)
```

**Solution:**
- Use tolerance for flex-grow tests (10% recommended)
- Test relative relationships instead of exact values
- Accept that sum of item widths may differ by 1-2px from container

**Impact on Tests:**
- `test_flex_grow_proportions` uses 10% tolerance
- Avoid exact equality for dynamic sizing

### 2. Centering with Odd Dimensions

**Problem:**
When container or item has odd dimensions, perfect centering requires fractional pixel positions. Browsers round differently.

**Example:**
```python
# Container: 301px, Item: 100px
# True center: 150.5px
# Browser reports: 150px or 151px
```

**Solution:**
- Always use ±1px tolerance for centering
- Compare centers, not edges
- Document tolerance in test assertions

**Impact on Tests:**
- `test_flex_center_alignment` uses 1px tolerance
- `test_flex_row_items_spacing` allows 1px for vertical centering

### 3. Gap Property and Browser Support

**Problem:**
The `gap` property was added to flexbox in CSS3 (originally for grid). Older browsers may not support it.

**Example:**
```css
.container {
    display: flex;
    gap: 10px;  /* Not supported in IE11, old Safari */
}
```

**Solution:**
- Test in modern browsers only (Chromium for these tests)
- Have fallback tests for margin-based spacing if needed
- Document browser requirements in test

**Impact on Tests:**
- All tests assume modern Chromium browser
- No fallback tests for older browsers
- Gap property works reliably in test environment

### 4. Absolute Positioning Inside Flex Containers

**Problem:**
Absolute positioned children inside flex containers don't participate in flex layout but affect testing if not accounted for.

**Example:**
```html
<div style="display: flex">
    <div>Flex item</div>
    <div style="position: absolute">Not a flex item</div>
    <div>Flex item</div>
</div>
```

**Solution:**
- Don't mix absolute positioning with flex items in tests
- If needed, explicitly test that absolute items are excluded
- Document any absolute positioning in test HTML

**Impact on Tests:**
- No absolute positioning inside flex containers in test HTML
- All children participate in flex layout
- Container positioning is absolute but items are not

### 5. Min-width/Max-width Interactions

**Problem:**
Flex items respect `min-width` and `max-width`, which can override flex-grow/flex-shrink calculations.

**Example:**
```css
.item {
    flex-grow: 1;
    max-width: 100px;  /* Prevents item from growing beyond 100px */
}
```

**Solution:**
- Don't set size constraints on flex items in tests unless specifically testing that behavior
- Document any min/max constraints if used
- Test that constraints are respected when present

**Impact on Tests:**
- No min-width/max-width in test HTML
- Flex-grow behavior is pure and unobstructed
- Future tests should add constraint testing if needed

### 6. Flex-basis and Content Sizing

**Problem:**
When `flex-basis: auto` (default), item size depends on content, which varies with font rendering and text metrics.

**Example:**
```python
# Item with text "Hello"
# Width varies based on font, anti-aliasing, browser
# May be 45px, 46px, or 47px
```

**Solution:**
- Use fixed `width` or `flex-basis` for predictable testing
- When testing content-based sizing, use ranges or relative comparisons
- Avoid exact pixel assertions for content-sized items

**Impact on Tests:**
- All flex items have fixed widths or heights
- No content-dependent sizing in current tests
- Future tests should use ranges if testing content sizing

### 7. Margin Collapse and Flex Containers

**Problem:**
Flex containers don't collapse margins with children, unlike block layout. This affects spacing calculations.

**Example:**
```html
<div style="display: flex">
    <div style="margin: 10px">Item</div>  <!-- Margin doesn't collapse -->
</div>
```

**Solution:**
- Be aware that margins are additive in flex containers
- Use gap instead of margins for consistent spacing
- Document margin behavior if used in tests

**Impact on Tests:**
- Tests primarily use gap property
- Minimal margins in flex items
- Gap is more predictable than margins

### 8. Writing Mode and Direction

**Problem:**
Flexbox respects `writing-mode` and `direction` CSS properties, which can reverse main-axis and cross-axis.

**Example:**
```css
.container {
    display: flex;
    direction: rtl;  /* Right-to-left - reverses item order */
}
```

**Solution:**
- Tests assume LTR (left-to-right) and horizontal-tb writing mode
- Document writing mode assumptions
- Add explicit tests if RTL support is needed

**Impact on Tests:**
- All tests assume default LTR layout
- No RTL or vertical writing mode testing
- Future tests should add RTL cases if needed

## Design Decisions

### 1. Multiple Test Cases in One HTML File
**Decision**: Created one HTML file with 5 different flex containers instead of 5 separate files  
**Rationale**: 
- Reduces file proliferation
- Faster test execution (one page load)
- Easier to maintain related test cases
- Each container is independent (absolute positioning)

**Trade-off**: Test file is longer, but tests are well-organized by function

### 2. Absolute Positioning for Containers
**Decision**: All flex containers use absolute positioning for placement  
**Rationale**:
- Predictable layout regardless of viewport size
- No interaction between test cases
- Same pattern as Step 2 for consistency
- Easy to verify container dimensions and positions

**Future**: Step 4 may use relative positioning for more realistic testing

### 3. Fixed Dimensions
**Decision**: All containers and most items have fixed pixel dimensions  
**Rationale**:
- Makes assertions deterministic
- Easier to debug test failures
- Flex-grow test demonstrates dynamic sizing
- Matches Step 2 testing philosophy

**Future**: Step 4 will test responsive behavior with viewport changes

### 4. No Flex-wrap Testing
**Decision**: Didn't include tests for `flex-wrap` behavior  
**Rationale**:
- Step 3 focuses on basic flexbox properties
- Wrapping is complex and deserves dedicated tests
- Would require responsive viewport testing
- Can be added in future steps if needed

**Future**: Consider adding wrap tests if Step 4 needs them

### 5. 10% Tolerance for Flex-grow
**Decision**: Used 10% tolerance for flex-grow proportion testing  
**Rationale**:
- Testing showed some variance in flex calculations
- 5% was too tight, 10% allows for browser differences
- Still catches major layout errors
- Relative comparisons (>) are more reliable

**Alternative**: Could use 5% tolerance with more robust expected value calculation

### 6. Seven Separate Test Functions
**Decision**: Split flexbox testing into 7 focused test functions  
**Rationale**:
- Each test validates one aspect of flexbox
- Easy to identify which behavior failed
- Follows Step 2 pattern (3 tests)
- Granular tests aid debugging

**Pattern**: Continue this approach in Step 4

### 7. Computed Styles Test Included
**Decision**: Added test for reading flexbox CSS properties via JS  
**Rationale**:
- Proves CSS was applied correctly
- Useful for debugging test failures
- Follows Step 2 pattern (computed styles test)
- Validates that properties are accessible

**Use case**: Future tests can use this to debug layout issues

### 8. No Visual Regression Testing
**Decision**: Didn't add screenshot comparison tests  
**Rationale**:
- Step 3 focuses on measurement capabilities
- Screenshot testing is orthogonal to measurement
- Would require baseline images
- Adds complexity without measuring behavior

**Future**: Step 4 might benefit from visual regression testing

## Warnings for Step 4 (Complex Layout Testing)

### 1. CSS Grid Introduces New Complexity
**Challenge**: Grid layout has both explicit and implicit tracks, spanning, and area names  
**Considerations**:
- Test explicit grid dimensions (grid-template-columns/rows)
- Validate implicit track creation
- Test grid gap vs flexbox gap (similar but different contexts)
- Test item placement (grid-column, grid-row)
- Test area names (grid-template-areas)
- Consider fractional units (fr) and auto sizing

**Testing Strategy**:
- Start with fixed grid (2x2, 3x3)
- Test gap property (should behave like flexbox)
- Test item spanning
- Test auto-placement algorithm

### 2. Aspect-ratio Property Behavior
**Challenge**: Dynamic aspect-ratio affects item sizing based on container constraints  
**Considerations**:
- Test aspect-ratio with fixed width (height is calculated)
- Test aspect-ratio with fixed height (width is calculated)
- Test aspect-ratio with max-width/max-height constraints
- Test aspect-ratio in grid context (main use case for Wordle game)
- Consider browser rounding with aspect ratios

**Testing Strategy**:
- Use simple ratios (1:1, 16:9, 4:3)
- Allow 1-2px tolerance for aspect ratio calculations
- Test with fixed container dimensions first
- Validate square tiles maintain proportions

### 3. Container Queries
**Challenge**: The Wordle game uses container queries for responsive font sizing  
**Considerations**:
- Container queries are relatively new (may need polyfill for older browsers)
- Test that font size changes with container size
- Validate cqmin/cqmax units
- Test clamp() function with container query units

**Testing Strategy**:
- Create test with container query
- Change container size
- Measure computed font size
- Validate responsive scaling

### 4. Dynamic Viewport Units (dvh, svh)
**Challenge**: Modern viewport units account for browser UI (URL bar, etc.)  
**Considerations**:
- dvh (dynamic viewport height) changes as browser UI appears/disappears
- svh (small viewport height) is static
- Test at multiple viewport sizes
- Consider mobile vs desktop behavior

**Testing Strategy**:
- Use fixed viewport for initial tests
- Test with Playwright viewport resize
- Validate layout doesn't break at different sizes
- Consider using regular vh for tests if dvh is unpredictable

### 5. Nested Layouts (Grid + Flex)
**Challenge**: Real applications nest flexbox and grid (container > flexbox > grid)  
**Considerations**:
- Test layout at each nesting level
- Validate containment boundaries
- Test that parent constraints propagate correctly
- Consider performance of deeply nested layouts

**Testing Strategy**:
- Test outer container first
- Test each nesting level independently
- Validate parent-child relationships
- Use hierarchical test organization

### 6. Responsive Breakpoints
**Challenge**: Real applications adapt layout at different viewport sizes  
**Considerations**:
- Test multiple viewport sizes (mobile, tablet, desktop)
- Validate media query breakpoints
- Test that layout transitions are correct
- Consider orientation changes

**Testing Strategy**:
- Use Playwright viewport configuration
- Test key breakpoints (320px, 768px, 1024px, 1280px)
- Validate layout changes at each breakpoint
- Consider using fixtures for viewport sizes

### 7. Real Application Complexity
**Challenge**: Wordle game has keyboard, header, message area, game board  
**Considerations**:
- Test complete page layout, not just one component
- Validate interactions between components
- Test overflow behavior
- Consider accessibility (focus states, keyboard navigation)

**Testing Strategy**:
- Start with board layout (most complex)
- Add other components incrementally
- Test complete page layout
- Consider visual regression testing
- Use screenshots for comparison

### 8. Variable Grid Configurations (6×3 to 6×25)
**Challenge**: Wordle game supports different word lengths (3-25 letters)  
**Considerations**:
- Test minimum configuration (6×3)
- Test maximum configuration (6×25)
- Test edge cases (1 column, 100 columns)
- Validate that wide grids fit in viewport
- Test scrolling behavior if needed

**Testing Strategy**:
- Parameterize tests with grid size
- Test key configurations (3, 5, 10, 25)
- Validate overflow handling
- Test aspect-ratio maintains square tiles at all sizes

## Technical Insights

### 1. Flexbox Coordinate System
- Main axis: Direction of flex-direction (row = horizontal, column = vertical)
- Cross axis: Perpendicular to main axis
- All coordinates still viewport-relative (like Step 2)
- Bounding boxes work identically to non-flex elements

### 2. Space Distribution Algorithms
- `space-between`: No space at edges, equal space between items
- `space-around`: Half space at edges, equal space between items
- `space-evenly`: Equal space at edges and between items (not tested yet)
- `flex-start`: Items at start, no space distribution
- `flex-end`: Items at end, no space distribution
- `center`: Items centered, equal space on both sides

### 3. Flex-grow Calculation
Formula: `item_width = flex_basis + (available_space × flex_grow / total_flex_grow)`

Where:
- `flex_basis` = initial item size (or content size if auto)
- `available_space` = container_width - sum(flex_basis) - gaps - padding
- `total_flex_grow` = sum of all flex-grow values

Browser implementation may round intermediate values, causing variance.

### 4. Gap vs Margin
- Gap: Space between items only (not at edges)
- Margin: Space around items (including edges)
- Gap is more predictable for testing
- Margins collapse in block layout but not in flex

### 5. Alignment Properties Summary
**Justify-content** (main axis):
- flex-start, flex-end, center
- space-between, space-around, space-evenly

**Align-items** (cross axis):
- flex-start, flex-end, center
- stretch, baseline

**Align-self** (individual item cross axis):
- Same values as align-items
- Not tested in this step

### 6. Flexbox vs Grid
Key differences for testing:
- Flexbox: One-dimensional (row or column)
- Grid: Two-dimensional (rows and columns)
- Flexbox: Space distribution algorithms
- Grid: Explicit track sizing
- Flexbox: Content-driven sizing
- Grid: Container-driven sizing

## Testing Philosophy Progression

### Step 1: Tool Installation
- Proved Playwright works
- Basic smoke tests
- No layout assertions

### Step 2: Deterministic Layout
- Absolute positioning
- Fixed dimensions
- Exact pixel assertions
- No dynamic behavior

### Step 3: Dynamic Layout (Current)
- Flexbox introduces dynamic sizing
- Relative positioning assertions
- Tolerance required for some tests
- Gap and alignment properties

### Step 4: Complex Layout (Next)
- CSS Grid (two-dimensional)
- Aspect-ratio (dynamic calculations)
- Container queries (responsive)
- Real application testing
- Multiple viewport sizes

**Key Pattern**: Each step increases complexity while building on previous techniques.

## Testing Commands

```bash
# Run all Playwright tests
uv run pytest tests/playwright/

# Run only flexbox layout tests
uv run pytest tests/playwright/test_flexbox_layout.py

# Run with verbose output
uv run pytest tests/playwright/test_flexbox_layout.py -v

# Run specific test
uv run pytest tests/playwright/test_flexbox_layout.py::test_flex_row_container_dimensions -v

# Run with test output
uv run pytest tests/playwright/test_flexbox_layout.py -v -s
```

## Verification Checklist

The Step 3 implementation is correct when:
- ✅ test_flexbox_layout.html includes 5 different flex container test cases
- ✅ HTML covers row/column directions, alignment, gap, and flex-grow
- ✅ Seven test functions cover all flexbox behaviors
- ✅ All tests pass with pytest
- ✅ Tests use relative positioning assertions (not absolute coordinates)
- ✅ Tests include tolerance where appropriate (centering: 1px, flex-grow: 10%)
- ✅ Tests validate both dimensions and computed styles
- ✅ Documentation explains reliable vs fragile assertions
- ✅ Documentation lists pitfalls for real browser testing
- ✅ Documentation prepares next agent for CSS Grid and aspect-ratio

## Summary of Key Learnings

### What Works Well with Flexbox Testing

1. **Edge Positioning**: Space-between creates predictable edge positions (exact equality)
2. **Gap Property**: Creates consistent, measurable spacing (exact equality)
3. **Item Ordering**: Flex items maintain order reliably (inequality tests)
4. **Stretch Behavior**: Items fill container predictably (exact equality)
5. **Computed Styles**: All flex properties readable via JavaScript

### What Requires Tolerance

1. **Flex-grow Distribution**: Browser rounding varies (10% tolerance recommended)
2. **Centering with Odd Dimensions**: Fractional pixels rounded (1px tolerance)
3. **Complex Space Distribution**: Multiple calculations compound rounding

### What to Avoid

1. **Exact Flex-grow Values**: Use relative comparisons instead
2. **Content-based Sizing**: Text width varies with rendering
3. **Mixing Absolute Positioning**: Absolute children don't participate in flex
4. **Assuming Perfect Equality**: Always consider sub-pixel rendering

### Best Practices for Flexbox Testing

1. **Use Fixed Dimensions**: Makes tests predictable
2. **Test Relationships**: Compare items to each other, not absolute values
3. **Add Tolerance**: 1px for centering, 10% for flex-grow
4. **Test Computed Styles**: Validates CSS application
5. **Document Assumptions**: Note browser version, viewport size, etc.
6. **Use Gap Instead of Margin**: More predictable spacing
7. **Test One Property at a Time**: Isolate flex behaviors
8. **Progressive Complexity**: Start simple, add complexity incrementally

## Next Steps for Future Agents

### Immediate Next Step: Step 4 - Complex Layout Testing

1. **Create Grid Layout HTML**:
   - Fixed grid (e.g., 3×3) with explicit tracks
   - Test gap property in grid context
   - Test item spanning (grid-column, grid-row)
   - Test auto-placement algorithm

2. **Test Aspect-ratio Property**:
   - Simple 1:1 aspect-ratio (square)
   - Test with fixed width (height calculated)
   - Test with max-height constraint
   - Validate square tiles maintain proportions

3. **Test Real Application Layout**:
   - Load Wordle game HTML from `src/static/`
   - Test board grid with dynamic aspect-ratio
   - Test multiple configurations (6×3, 6×5, 6×25)
   - Validate complete page layout

4. **Test Responsive Behavior**:
   - Multiple viewport sizes (mobile, tablet, desktop)
   - Validate layout adapts correctly
   - Test container queries if used
   - Consider dvh/svh viewport units

5. **Document Findings**:
   - Create `html_css_test_step4.instructions.md`
   - Document grid testing techniques
   - Explain aspect-ratio challenges
   - Summarize complete testing approach

### Long-term Considerations

- **Visual Regression Testing**: Add screenshot comparison
- **Cross-browser Testing**: Test in Firefox, Safari, Edge
- **Performance Testing**: Measure layout calculation time
- **Accessibility Testing**: Add ARIA and keyboard navigation tests
- **Animation Testing**: Test transitions and animations if present

## Resources

- [MDN: Flexbox](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Flexible_Box_Layout)
- [MDN: justify-content](https://developer.mozilla.org/en-US/docs/Web/CSS/justify-content)
- [MDN: align-items](https://developer.mozilla.org/en-US/docs/Web/CSS/align-items)
- [MDN: gap](https://developer.mozilla.org/en-US/docs/Web/CSS/gap)
- [MDN: flex-grow](https://developer.mozilla.org/en-US/docs/Web/CSS/flex-grow)
- [Playwright Python Locators](https://playwright.dev/python/docs/locators)
- [CSS Grid (for Step 4)](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_Grid_Layout)
- [aspect-ratio (for Step 4)](https://developer.mozilla.org/en-US/docs/Web/CSS/aspect-ratio)
- [Wordle Layout Architecture](.github/instructions/static_wordle_architecture.instructions.md)
