"""Test for basic HTML+CSS box layout measurement.

This test validates that Playwright can accurately measure
layout properties like dimensions, position, and visibility
for a simple box element.

Step 2 of the HTML/CSS layout testing progression.
"""

import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def box_layout_page_path():
    """Return the path to the box layout test HTML page."""
    return Path(__file__).parent / "test_box_layout.html"


def test_box_layout_dimensions(page, box_layout_page_path):
    """Test that we can measure basic box dimensions accurately.
    
    This test validates:
    - Element is visible on page
    - Bounding box dimensions match expected values
    - Position matches expected coordinates
    - Box has non-zero size
    """
    # Navigate to the test page
    page.goto(f"file://{box_layout_page_path}")
    
    # Verify the page loaded
    assert page.title() == "Box Layout Test"
    
    # Get the main test box
    box = page.locator("#main-box")
    
    # Verify the box is visible
    assert box.is_visible(), "Test box should be visible"
    
    # Get bounding box (returns dict with x, y, width, height)
    bbox = box.bounding_box()
    assert bbox is not None, "Bounding box should exist"
    
    # Verify dimensions match CSS (200px width, 150px height)
    # Note: With box-sizing: border-box, the bounding box returns the content + padding + border
    # which matches the specified width/height values
    assert bbox["width"] == 200, f"Expected width 200px, got {bbox['width']}px"
    assert bbox["height"] == 150, f"Expected height 150px, got {bbox['height']}px"
    
    # Verify position matches CSS (top: 50px, left: 100px)
    assert bbox["x"] == 100, f"Expected x position 100px, got {bbox['x']}px"
    assert bbox["y"] == 50, f"Expected y position 50px, got {bbox['y']}px"
    
    # Verify box has non-zero size (sanity check)
    assert bbox["width"] > 0, "Box width must be greater than 0"
    assert bbox["height"] > 0, "Box height must be greater than 0"


def test_box_computed_styles(page, box_layout_page_path):
    """Test that we can read computed CSS styles accurately.
    
    This test validates:
    - Computed styles can be read via JavaScript evaluation
    - Background color matches expected value
    - Border width matches expected value
    - Padding matches expected value
    """
    # Navigate to the test page
    page.goto(f"file://{box_layout_page_path}")
    
    # Get the main test box
    box = page.locator("#main-box")
    
    # Use JavaScript to get computed styles
    computed_style = page.evaluate("""
        () => {
            const element = document.getElementById('main-box');
            const style = window.getComputedStyle(element);
            return {
                backgroundColor: style.backgroundColor,
                borderWidth: style.borderWidth,
                padding: style.padding,
                width: style.width,
                height: style.height
            };
        }
    """)
    
    # Verify computed styles match CSS
    # Background color: #4CAF50 = rgb(76, 175, 80)
    assert computed_style["backgroundColor"] == "rgb(76, 175, 80)", \
        f"Expected background color rgb(76, 175, 80), got {computed_style['backgroundColor']}"
    
    # Border width should be 3px
    assert computed_style["borderWidth"] == "3px", \
        f"Expected border width 3px, got {computed_style['borderWidth']}"
    
    # Padding should be 20px
    assert computed_style["padding"] == "20px", \
        f"Expected padding 20px, got {computed_style['padding']}"
    
    # Width and height should match CSS values
    assert computed_style["width"] == "200px", \
        f"Expected width 200px, got {computed_style['width']}"
    assert computed_style["height"] == "150px", \
        f"Expected height 150px, got {computed_style['height']}"


def test_nested_element_layout(page, box_layout_page_path):
    """Test that nested elements are positioned correctly.
    
    This test validates:
    - Text element inside box is visible
    - Text position is relative to parent box
    - Text dimensions are reasonable
    """
    # Navigate to the test page
    page.goto(f"file://{box_layout_page_path}")
    
    # Get the text element inside the box
    text_element = page.locator("#text-content")
    
    # Verify it's visible
    assert text_element.is_visible(), "Text content should be visible"
    
    # Get its text content
    assert text_element.text_content() == "Test Box Content"
    
    # Get bounding boxes for both elements
    box_bbox = page.locator("#main-box").bounding_box()
    text_bbox = text_element.bounding_box()
    
    assert box_bbox is not None, "Box bounding box should exist"
    assert text_bbox is not None, "Text bounding box should exist"
    
    # Verify text is inside the box (accounting for padding)
    # Box starts at x=100, text should start at x=100+3(border)+20(padding)=123
    assert text_bbox["x"] >= box_bbox["x"] + 3 + 20, \
        "Text should be positioned inside box with padding"
    
    # Text should be vertically inside the box
    assert text_bbox["y"] >= box_bbox["y"] + 3 + 20, \
        "Text should be positioned inside box with padding"
    
    # Text should not exceed box boundaries
    assert text_bbox["x"] + text_bbox["width"] <= box_bbox["x"] + box_bbox["width"] - 3, \
        "Text should not overflow box horizontally"
    assert text_bbox["y"] + text_bbox["height"] <= box_bbox["y"] + box_bbox["height"] - 3, \
        "Text should not overflow box vertically"
    
    # Sanity check: text has reasonable dimensions
    assert text_bbox["width"] > 0, "Text width must be greater than 0"
    assert text_bbox["height"] > 0, "Text height must be greater than 0"
