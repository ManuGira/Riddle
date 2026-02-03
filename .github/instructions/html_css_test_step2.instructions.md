# HTML/CSS Layout Testing with Playwright - Step 2 Summary

## Overview
This document describes the completion of Step 2: Creating minimal HTML+CSS layout testing with Playwright. This builds upon the foundational setup from Step 1 and introduces actual layout measurement and assertion capabilities.

## What Was Added

### 1. Test HTML File (test_box_layout.html)
Created a minimal, deterministic HTML page with simple box layout:

**Key Features:**
- **No flexbox**: Uses absolute positioning for predictable layout
- **Fixed dimensions**: 200px width × 150px height box
- **Fixed position**: top: 50px, left: 100px
- **Border and padding**: 3px border, 20px padding
- **Nested element**: Text content inside the box
- **box-sizing: border-box**: CSS box model where width/height include border and padding

**Design Rationale:**
- Absolute positioning ensures deterministic layout regardless of viewport
- Fixed pixel values make assertions straightforward
- border-box sizing simplifies dimension calculations
- Nested element tests layout measurement at multiple levels

### 2. Test Suite (test_box_layout.py)
Created three comprehensive tests that validate layout measurement capabilities:

#### Test 1: test_box_layout_dimensions
Validates that Playwright can accurately measure:
- **Element visibility**: Box is rendered and visible
- **Bounding box dimensions**: Width and height match expected values
- **Position**: X and Y coordinates match CSS positioning
- **Non-zero size**: Sanity check that dimensions are positive

**Key Learning:**
The `bounding_box()` method returns the visual bounding box including content, padding, and border. With `box-sizing: border-box`, this matches the CSS width/height values exactly (200px × 150px).

#### Test 2: test_box_computed_styles
Validates that Playwright can read computed CSS styles via JavaScript evaluation:
- **Background color**: Verifies rgb(76, 175, 80) matches #4CAF50
- **Border width**: Confirms 3px border
- **Padding**: Confirms 20px padding
- **Dimensions**: Confirms 200px width and 150px height

**Key Learning:**
JavaScript `window.getComputedStyle()` provides access to all computed CSS properties. Colors are returned in RGB format, not hex. This test demonstrates that we can inspect any CSS property programmatically.

#### Test 3: test_nested_element_layout
Validates that Playwright can measure nested element positioning:
- **Nested element visibility**: Text element is visible
- **Content verification**: Text matches expected value
- **Relative positioning**: Text is positioned inside parent box
- **Padding respect**: Text starts at parent's edge + border + padding
- **No overflow**: Text stays within parent boundaries

**Key Learning:**
Bounding boxes can be compared to validate parent-child relationships. The test confirms that padding (20px) and border (3px) are correctly applied, placing the text at coordinates (123, 73) relative to viewport (100+3+20, 50+3+20).

## Layout Measurement Techniques

### 1. Bounding Box API
```python
bbox = page.locator("#element").bounding_box()
# Returns: {"x": int, "y": int, "width": int, "height": int}
```

**What it measures:**
- Pixel coordinates relative to viewport
- Total rendered dimensions including border (with box-sizing: border-box)
- Always returns integers (rounded to nearest pixel)

**Use cases:**
- Position validation
- Size validation
- Element overlap detection
- Viewport-relative positioning

### 2. Computed Styles API
```python
styles = page.evaluate("""
    () => {
        const el = document.getElementById('element');
        const style = window.getComputedStyle(el);
        return {
            width: style.width,
            backgroundColor: style.backgroundColor,
            // ... any CSS property
        };
    }
""")
```

**What it measures:**
- Final computed CSS values after cascade
- Colors in RGB/RGBA format
- Dimensions in CSS units (px, em, etc.)
- All inherited and default values

**Use cases:**
- CSS property validation
- Color verification
- Font size/family checks
- Any style-based assertion

### 3. Element Visibility API
```python
is_visible = page.locator("#element").is_visible()
# Returns: bool
```

**What it checks:**
- Element is rendered (display != none)
- Has non-zero dimensions
- Opacity > 0
- Not hidden by visibility: hidden

**Use cases:**
- Sanity check before measurement
- Visibility state validation
- Conditional UI testing

## Assumptions Validated

### 1. Box Model Behavior
✅ **Assumption**: With `box-sizing: border-box`, the bounding box dimensions equal CSS width/height  
✅ **Validation**: Test measures 200×150px box and confirms dimensions match exactly  
✅ **Conclusion**: Playwright's bounding_box() correctly implements border-box semantics

### 2. Absolute Positioning Accuracy
✅ **Assumption**: Absolute positioning creates pixel-perfect predictable layout  
✅ **Validation**: Box positioned at (100, 50) measures exactly at those coordinates  
✅ **Conclusion**: No browser-specific positioning quirks; coordinates are reliable

### 3. Nested Element Layout
✅ **Assumption**: Nested elements respect parent padding and borders  
✅ **Validation**: Text element correctly positioned at parent offset + border + padding  
✅ **Conclusion**: Parent-child layout relationships can be tested through bounding box comparisons

### 4. Computed Style Accuracy
✅ **Assumption**: window.getComputedStyle() returns accurate final values  
✅ **Validation**: All CSS properties (color, border, padding, dimensions) match expected values  
✅ **Conclusion**: Computed styles are reliable for assertion-based testing

### 5. Color Value Representation
✅ **Assumption**: Colors are returned in RGB format, not as specified  
✅ **Validation**: #4CAF50 returns as rgb(76, 175, 80)  
✅ **Conclusion**: Tests must expect RGB format for color assertions

## Design Decisions

### 1. No Flexbox Yet
**Decision**: Use absolute positioning instead of flexbox  
**Rationale**: Isolates layout measurement from flexbox complexity; tests exactly one thing  
**Next Step**: Step 3 will introduce flexbox testing

### 2. Fixed Pixel Values
**Decision**: All dimensions and positions use fixed pixel values  
**Rationale**: Makes assertions deterministic; no viewport dependency  
**Next Step**: Step 3+ will test responsive behavior with different viewports

### 3. Border-Box Sizing
**Decision**: Use `box-sizing: border-box` globally  
**Rationale**: Modern CSS best practice; simplifies dimension calculations  
**Impact**: Bounding box dimensions match CSS width/height exactly

### 4. Separate Test File
**Decision**: Created new `test_box_layout.html` instead of modifying existing test page  
**Rationale**: Each test file should have a focused purpose; easier to maintain  
**Pattern**: Continue creating separate HTML files for each test scenario

### 5. Three-Test Structure
**Decision**: Split functionality into three separate test functions  
**Rationale**: Each test validates one category of measurement; easier to debug failures  
**Pattern**: Future tests should follow similar focused structure

## Warnings for Step 3 (Flexbox Testing)

### 1. Flexbox Introduces Non-Determinism
**Challenge**: Flexbox distributes space dynamically based on content and container size  
**Consideration**: Tests may need to:
  - Verify relative relationships rather than exact values
  - Use tolerance ranges instead of exact equality
  - Test multiple viewport sizes to validate responsive behavior

### 2. Alignment Properties
**Challenge**: Flexbox alignment (justify-content, align-items) affects element positions  
**Consideration**: Tests should:
  - Verify elements are centered/aligned as expected
  - Check spacing between flex items
  - Validate flex-direction behavior (row vs column)

### 3. Flex Growing and Shrinking
**Challenge**: flex-grow and flex-shrink change element sizes dynamically  
**Consideration**: Tests should:
  - Verify elements expand to fill available space
  - Check that proportions are maintained
  - Validate behavior with different container sizes

### 4. Gap Property
**Challenge**: gap property creates space between flex items  
**Consideration**: Tests should:
  - Verify consistent spacing between items
  - Check that gap doesn't affect external margins
  - Validate gap behavior with wrap

### 5. Container vs Item Properties
**Challenge**: Flexbox has properties on both container and items  
**Consideration**: Tests should:
  - Separate container property tests from item property tests
  - Verify interaction between container and item properties
  - Test edge cases (empty flex containers, single items, etc.)

### 6. Viewport Dependency
**Challenge**: Flexbox may behave differently at different viewport sizes  
**Consideration**: Tests may need:
  - Multiple viewport configurations in fixtures
  - Responsive breakpoint testing
  - Mobile vs desktop layout validation

**Note**: The existing Playwright config sets viewport to 1280×720. Step 3 tests should consider whether this is appropriate for flexbox testing or if multiple viewport sizes are needed.

## Technical Insights

### 1. Bounding Box Coordinate System
- Origin (0, 0) is top-left of viewport
- All coordinates are viewport-relative (not document-relative)
- Scrolling affects coordinates
- For our absolute-positioned box at (100, 50), coordinates are predictable

### 2. Box-Sizing Impact
- `border-box`: width/height include border and padding
- `content-box`: width/height exclude border and padding
- Our tests assume border-box (modern CSS standard)
- Future tests should document box-sizing assumptions

### 3. Playwright's Measurement APIs
- `bounding_box()`: Visual dimensions including all visual elements
- `element.evaluate()`: Access to full DOM API
- `page.evaluate()`: Access to window and document APIs
- All measurements return in pixels (integers)

### 4. Testing Philosophy
- Test deterministic layouts first (Step 2)
- Add dynamic layouts second (Step 3: flexbox)
- Add complex layouts last (Step 4: real application)
- Each step builds on previous measurement techniques

## Testing Commands

```bash
# Run all Playwright tests
uv run pytest tests/playwright/

# Run only box layout tests
uv run pytest tests/playwright/test_box_layout.py

# Run with verbose output
uv run pytest tests/playwright/test_box_layout.py -v

# Run specific test
uv run pytest tests/playwright/test_box_layout.py::test_box_layout_dimensions -v
```

## Verification Checklist

The Step 2 implementation is correct when:
- ✅ test_box_layout.html uses absolute positioning (no flexbox)
- ✅ All dimensions are fixed pixel values
- ✅ Three test functions cover: dimensions, computed styles, nested elements
- ✅ All tests pass with pytest
- ✅ Tests use bounding_box() for dimension measurement
- ✅ Tests use window.getComputedStyle() for CSS property validation
- ✅ Tests verify parent-child layout relationships
- ✅ Documentation explains measurement techniques and design decisions

## Next Steps

### Step 3: Flexbox Container Testing
The next step should:
1. Create HTML with flexbox containers (row and column layouts)
2. Test flex properties: justify-content, align-items, gap
3. Validate element spacing and alignment
4. Test with minimal responsive behavior (if needed)
5. Document flexbox-specific measurement challenges

**Key Questions to Answer in Step 3:**
- How do we test relative positioning instead of absolute coordinates?
- What tolerance should we use for dynamic sizing?
- Do we need multiple viewport sizes for flexbox testing?
- How do we validate alignment properties (center, space-between, etc.)?

### Step 4: Complex Layout (Real Application)
The final step will:
1. Test the actual Wordle game layout from `src/static/`
2. Validate CSS Grid with dynamic aspect-ratio
3. Test various grid configurations (6×3, 6×5, 6×25)
4. Verify responsive behavior across viewport sizes
5. Reference architecture docs in `.github/instructions/static_wordle_architecture.instructions.md`

## Resources

- [Playwright Python Locators](https://playwright.dev/python/docs/locators)
- [Element Handles and Bounding Boxes](https://playwright.dev/python/docs/api/class-elementhandle#element-handle-bounding-box)
- [Page Evaluation](https://playwright.dev/python/docs/evaluating)
- [MDN: window.getComputedStyle()](https://developer.mozilla.org/en-US/docs/Web/API/Window/getComputedStyle)
- [MDN: box-sizing](https://developer.mozilla.org/en-US/docs/Web/CSS/box-sizing)
