"""Test for flexbox layout measurement with Playwright.

This test validates that Playwright can accurately measure
flexbox layouts including container properties, item positioning,
alignment, spacing, and flex-grow behavior.

Step 3 of the HTML/CSS layout testing progression.
"""

import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def flexbox_layout_page_path():
    """Return the path to the flexbox layout test HTML page."""
    return Path(__file__).parent / "test_flexbox_layout.html"


def test_flex_row_container_dimensions(page, flexbox_layout_page_path):
    """Test that flex row container has correct dimensions.
    
    This test validates:
    - Container is visible
    - Container dimensions match CSS values
    - Container is positioned correctly
    """
    page.goto(f"file://{flexbox_layout_page_path}")
    
    # Verify page loaded
    assert page.title() == "Flexbox Layout Test"
    
    # Get the flex row container
    container = page.locator("#row-container")
    assert container.is_visible(), "Flex row container should be visible"
    
    # Get bounding box
    bbox = container.bounding_box()
    assert bbox is not None, "Container bounding box should exist"
    
    # Verify dimensions (600px width, 100px height)
    assert bbox["width"] == 600, f"Expected width 600px, got {bbox['width']}px"
    assert bbox["height"] == 100, f"Expected height 100px, got {bbox['height']}px"
    
    # Verify position (top: 20px, left: 20px)
    assert bbox["x"] == 20, f"Expected x position 20px, got {bbox['x']}px"
    assert bbox["y"] == 20, f"Expected y position 20px, got {bbox['y']}px"


def test_flex_row_items_spacing(page, flexbox_layout_page_path):
    """Test that flex row items are spaced correctly with space-between.
    
    This test validates:
    - All flex items are visible
    - Items are positioned horizontally within container
    - Items are spaced with justify-content: space-between
    - Items are vertically centered (align-items: center)
    """
    page.goto(f"file://{flexbox_layout_page_path}")
    
    # Get container and items
    container = page.locator("#row-container")
    item1 = page.locator("#row-item-1")
    item2 = page.locator("#row-item-2")
    item3 = page.locator("#row-item-3")
    
    # Verify all visible
    assert item1.is_visible(), "Item 1 should be visible"
    assert item2.is_visible(), "Item 2 should be visible"
    assert item3.is_visible(), "Item 3 should be visible"
    
    # Get bounding boxes
    container_bbox = container.bounding_box()
    item1_bbox = item1.bounding_box()
    item2_bbox = item2.bounding_box()
    item3_bbox = item3.bounding_box()
    
    assert all(b is not None for b in [container_bbox, item1_bbox, item2_bbox, item3_bbox]), \
        "All bounding boxes should exist"
    
    # Verify items are inside container horizontally
    assert item1_bbox["x"] >= container_bbox["x"], "Item 1 should be inside container"
    assert item3_bbox["x"] + item3_bbox["width"] <= container_bbox["x"] + container_bbox["width"], \
        "Item 3 should be inside container"
    
    # Verify space-between: first item at start, last item at end
    # Item 1 should be at the left edge of container
    assert item1_bbox["x"] == container_bbox["x"], \
        "With space-between, first item should be at container start"
    
    # Item 3 should be at the right edge of container
    assert item3_bbox["x"] + item3_bbox["width"] == container_bbox["x"] + container_bbox["width"], \
        "With space-between, last item should be at container end"
    
    # Verify item 2 is between items 1 and 3
    assert item1_bbox["x"] < item2_bbox["x"] < item3_bbox["x"], \
        "Items should be ordered left to right"
    
    # Verify vertical centering (align-items: center)
    # All items should have same vertical center
    container_center_y = container_bbox["y"] + container_bbox["height"] / 2
    
    for item_bbox, item_name in [(item1_bbox, "Item 1"), (item2_bbox, "Item 2"), (item3_bbox, "Item 3")]:
        item_center_y = item_bbox["y"] + item_bbox["height"] / 2
        # Allow 1px tolerance for rounding
        assert abs(item_center_y - container_center_y) <= 1, \
            f"{item_name} should be vertically centered in container"


def test_flex_column_layout(page, flexbox_layout_page_path):
    """Test that flex column layout arranges items vertically.
    
    This test validates:
    - Items are arranged vertically
    - Items respect gap property
    - Items stretch to container width (align-items: stretch)
    - Items start at top (justify-content: flex-start)
    """
    page.goto(f"file://{flexbox_layout_page_path}")
    
    # Get container and items
    container = page.locator("#column-container")
    item1 = page.locator("#col-item-1")
    item2 = page.locator("#col-item-2")
    item3 = page.locator("#col-item-3")
    
    # Get bounding boxes
    container_bbox = container.bounding_box()
    item1_bbox = item1.bounding_box()
    item2_bbox = item2.bounding_box()
    item3_bbox = item3.bounding_box()
    
    assert all(b is not None for b in [container_bbox, item1_bbox, item2_bbox, item3_bbox]), \
        "All bounding boxes should exist"
    
    # Verify vertical ordering
    assert item1_bbox["y"] < item2_bbox["y"] < item3_bbox["y"], \
        "Items should be ordered top to bottom"
    
    # Verify gap between items (10px gap + 15px padding)
    # Item 1 should start at container top + padding
    expected_item1_y = container_bbox["y"] + 15  # padding
    assert item1_bbox["y"] == expected_item1_y, \
        f"Item 1 should start at y={expected_item1_y}, got {item1_bbox['y']}"
    
    # Gap between items should be 10px
    gap_1_2 = item2_bbox["y"] - (item1_bbox["y"] + item1_bbox["height"])
    gap_2_3 = item3_bbox["y"] - (item2_bbox["y"] + item2_bbox["height"])
    
    assert gap_1_2 == 10, f"Expected 10px gap between items 1-2, got {gap_1_2}px"
    assert gap_2_3 == 10, f"Expected 10px gap between items 2-3, got {gap_2_3}px"
    
    # Verify items stretch to container width (minus padding)
    expected_width = container_bbox["width"] - 2 * 15  # container width - 2*padding
    
    for item_bbox, item_name in [(item1_bbox, "Item 1"), (item2_bbox, "Item 2"), (item3_bbox, "Item 3")]:
        assert item_bbox["width"] == expected_width, \
            f"{item_name} should stretch to {expected_width}px, got {item_bbox['width']}px"


def test_flex_center_alignment(page, flexbox_layout_page_path):
    """Test that flex container centers item both horizontally and vertically.
    
    This test validates:
    - Item is centered horizontally (justify-content: center)
    - Item is centered vertically (align-items: center)
    """
    page.goto(f"file://{flexbox_layout_page_path}")
    
    # Get container and centered item
    container = page.locator("#center-container")
    item = page.locator("#center-item")
    
    # Get bounding boxes
    container_bbox = container.bounding_box()
    item_bbox = item.bounding_box()
    
    assert container_bbox is not None, "Container bounding box should exist"
    assert item_bbox is not None, "Item bounding box should exist"
    
    # Calculate centers
    container_center_x = container_bbox["x"] + container_bbox["width"] / 2
    container_center_y = container_bbox["y"] + container_bbox["height"] / 2
    
    item_center_x = item_bbox["x"] + item_bbox["width"] / 2
    item_center_y = item_bbox["y"] + item_bbox["height"] / 2
    
    # Verify centering (allow 1px tolerance for rounding)
    assert abs(item_center_x - container_center_x) <= 1, \
        f"Item should be horizontally centered: container center={container_center_x}, item center={item_center_x}"
    assert abs(item_center_y - container_center_y) <= 1, \
        f"Item should be vertically centered: container center={container_center_y}, item center={item_center_y}"


def test_flex_gap_property(page, flexbox_layout_page_path):
    """Test that gap property creates consistent spacing between items.
    
    This test validates:
    - Gap creates 20px spacing between items
    - Gap doesn't affect external margins
    - Items are positioned correctly with padding and gap
    """
    page.goto(f"file://{flexbox_layout_page_path}")
    
    # Get container and items
    container = page.locator("#gap-container")
    item1 = page.locator("#gap-item-1")
    item2 = page.locator("#gap-item-2")
    item3 = page.locator("#gap-item-3")
    
    # Get bounding boxes
    container_bbox = container.bounding_box()
    item1_bbox = item1.bounding_box()
    item2_bbox = item2.bounding_box()
    item3_bbox = item3.bounding_box()
    
    assert all(b is not None for b in [container_bbox, item1_bbox, item2_bbox, item3_bbox]), \
        "All bounding boxes should exist"
    
    # Verify first item starts at padding offset
    expected_item1_x = container_bbox["x"] + 10  # padding
    assert item1_bbox["x"] == expected_item1_x, \
        f"Item 1 should start at x={expected_item1_x}, got {item1_bbox['x']}"
    
    # Verify gap between items is 20px
    gap_1_2 = item2_bbox["x"] - (item1_bbox["x"] + item1_bbox["width"])
    gap_2_3 = item3_bbox["x"] - (item2_bbox["x"] + item2_bbox["width"])
    
    assert gap_1_2 == 20, f"Expected 20px gap between items 1-2, got {gap_1_2}px"
    assert gap_2_3 == 20, f"Expected 20px gap between items 2-3, got {gap_2_3}px"
    
    # Verify items are horizontally ordered
    assert item1_bbox["x"] < item2_bbox["x"] < item3_bbox["x"], \
        "Items should be ordered left to right"


def test_flex_grow_proportions(page, flexbox_layout_page_path):
    """Test that flex-grow distributes space proportionally.
    
    This test validates:
    - Items with flex-grow: 2 are larger than items with flex-grow: 1
    - Items fill available space accounting for gap
    - Proportions are approximately correct (2:1 ratio for large:small)
    """
    page.goto(f"file://{flexbox_layout_page_path}")
    
    # Get container and items
    container = page.locator("#grow-container")
    item1 = page.locator("#grow-item-1")  # flex-grow: 1
    item2 = page.locator("#grow-item-2")  # flex-grow: 2
    item3 = page.locator("#grow-item-3")  # flex-grow: 1
    
    # Get bounding boxes
    container_bbox = container.bounding_box()
    item1_bbox = item1.bounding_box()
    item2_bbox = item2.bounding_box()
    item3_bbox = item3.bounding_box()
    
    assert all(b is not None for b in [container_bbox, item1_bbox, item2_bbox, item3_bbox]), \
        "All bounding boxes should exist"
    
    # Verify item 2 (flex-grow: 2) is larger than items 1 and 3 (flex-grow: 1)
    assert item2_bbox["width"] > item1_bbox["width"], \
        "Item with flex-grow: 2 should be wider than item with flex-grow: 1"
    assert item2_bbox["width"] > item3_bbox["width"], \
        "Item with flex-grow: 2 should be wider than item with flex-grow: 1"
    
    # Verify items 1 and 3 have similar widths (both flex-grow: 1)
    # Allow small tolerance for rounding
    assert abs(item1_bbox["width"] - item3_bbox["width"]) <= 2, \
        f"Items with same flex-grow should have similar widths: item1={item1_bbox['width']}, item3={item3_bbox['width']}"
    
    # Verify approximate 2:1 ratio
    # Total flex units: 1 + 2 + 1 = 4
    # Available space: container width - 2*padding - 2*gap
    available_width = container_bbox["width"] - 2 * 10 - 2 * 10  # 2*padding + 2*gap
    
    # Expected widths (approximately)
    expected_small_width = available_width / 4  # 1 unit
    expected_large_width = 2 * available_width / 4  # 2 units
    
    # Allow 10% tolerance for flex calculations
    tolerance = 0.1
    
    assert abs(item1_bbox["width"] - expected_small_width) / expected_small_width <= tolerance, \
        f"Item 1 width should be approximately {expected_small_width}px, got {item1_bbox['width']}px"
    
    assert abs(item2_bbox["width"] - expected_large_width) / expected_large_width <= tolerance, \
        f"Item 2 width should be approximately {expected_large_width}px, got {item2_bbox['width']}px"
    
    assert abs(item3_bbox["width"] - expected_small_width) / expected_small_width <= tolerance, \
        f"Item 3 width should be approximately {expected_small_width}px, got {item3_bbox['width']}px"
    
    # Verify items fill container accounting for gaps
    total_item_width = item1_bbox["width"] + item2_bbox["width"] + item3_bbox["width"]
    total_gap = 2 * 10  # two gaps between three items
    total_padding = 2 * 10  # left and right padding
    
    expected_total = container_bbox["width"] - total_padding - total_gap
    
    # Allow 2px tolerance for rounding
    assert abs(total_item_width - expected_total) <= 2, \
        f"Total item width ({total_item_width}) + gaps + padding should equal container width ({container_bbox['width']})"


def test_flex_computed_styles(page, flexbox_layout_page_path):
    """Test that we can read flexbox-related computed styles.
    
    This test validates:
    - Can read display: flex property
    - Can read flex-direction property
    - Can read justify-content property
    - Can read align-items property
    - Can read gap property
    """
    page.goto(f"file://{flexbox_layout_page_path}")
    
    # Test row container styles
    row_styles = page.evaluate("""
        () => {
            const element = document.getElementById('row-container');
            const style = window.getComputedStyle(element);
            return {
                display: style.display,
                flexDirection: style.flexDirection,
                justifyContent: style.justifyContent,
                alignItems: style.alignItems
            };
        }
    """)
    
    assert row_styles["display"] == "flex", \
        f"Expected display: flex, got {row_styles['display']}"
    assert row_styles["flexDirection"] == "row", \
        f"Expected flex-direction: row, got {row_styles['flexDirection']}"
    assert row_styles["justifyContent"] == "space-between", \
        f"Expected justify-content: space-between, got {row_styles['justifyContent']}"
    assert row_styles["alignItems"] == "center", \
        f"Expected align-items: center, got {row_styles['alignItems']}"
    
    # Test column container styles
    col_styles = page.evaluate("""
        () => {
            const element = document.getElementById('column-container');
            const style = window.getComputedStyle(element);
            return {
                display: style.display,
                flexDirection: style.flexDirection,
                justifyContent: style.justifyContent,
                alignItems: style.alignItems,
                gap: style.gap
            };
        }
    """)
    
    assert col_styles["display"] == "flex", \
        f"Expected display: flex, got {col_styles['display']}"
    assert col_styles["flexDirection"] == "column", \
        f"Expected flex-direction: column, got {col_styles['flexDirection']}"
    assert col_styles["justifyContent"] == "flex-start", \
        f"Expected justify-content: flex-start, got {col_styles['justifyContent']}"
    assert col_styles["alignItems"] == "stretch", \
        f"Expected align-items: stretch, got {col_styles['alignItems']}"
    assert col_styles["gap"] == "10px", \
        f"Expected gap: 10px, got {col_styles['gap']}"
