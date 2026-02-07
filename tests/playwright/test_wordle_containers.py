"""Test Wordle container overlap detection using Playwright.

This test validates that containers (header, board, keyboard) do not overlap
in the real Wordle application for different grid sizes and viewport layouts.

Tests:
- Phone layout (400×844): 6×3 and 6×25 grids
- Desktop layout (1280×720): 6×3 and 6×25 grids

Expected behavior:
- Containers should not overlap (each should have distinct boundaries)
- Phone layout should work correctly
- Desktop 6×3 may show grid overflow (which we're testing for)
- Desktop 6×25 should work correctly

NOTE: Tests the actual production HTML and CSS files from src/static/.
"""

import pytest
from pathlib import Path


@pytest.fixture(scope="module")
def static_dir():
    """Return the path to the static directory with production files."""
    return Path(__file__).parent.parent.parent / "src" / "static"


def check_tiles_are_square(page, test_name, tolerance_px=1):
    """Check if all tiles in the grid are square (width ≈ height).
    
    Args:
        page: Playwright page object
        test_name: Name of the test for reporting
        tolerance_px: Maximum allowed difference between width and height in pixels
    
    Returns a dict with test results including:
    - non_square_tiles: list of tiles that are not square
    - tile_measurements: list of all tile dimensions
    - passed: bool indicating if all tiles are square
    """
    # Get all tile dimensions
    tile_data = page.evaluate("""() => {
        const tiles = document.querySelectorAll('.board-grid .tile');
        const measurements = [];
        
        tiles.forEach((tile, index) => {
            const rect = tile.getBoundingClientRect();
            measurements.push({
                index,
                row: tile.dataset.row,
                col: tile.dataset.col,
                width: rect.width,
                height: rect.height,
                aspect_ratio: rect.width / rect.height
            });
        });
        
        return {
            tile_count: tiles.length,
            tiles: measurements
        };
    }""")
    
    # Check which tiles are not square
    non_square_tiles = []
    for tile in tile_data['tiles']:
        width_height_diff = abs(tile['width'] - tile['height'])
        if width_height_diff > tolerance_px:
            non_square_tiles.append({
                'index': tile['index'],
                'row': tile['row'],
                'col': tile['col'],
                'width': tile['width'],
                'height': tile['height'],
                'difference': width_height_diff,
                'aspect_ratio': tile['aspect_ratio']
            })
    
    result = {
        'test_name': test_name,
        'passed': len(non_square_tiles) == 0,
        'non_square_tiles': non_square_tiles,
        'tile_count': tile_data['tile_count'],
        'tolerance_px': tolerance_px
    }
    
    return result


def check_containers_not_overlapping(page, test_name):
    """Check if header, board, and keyboard containers are not overlapping.
    
    Returns a dict with test results including:
    - overlaps: list of detected overlaps
    - measurements: dict of container positions
    - passed: bool indicating if test passed
    """
    # Get bounding boxes for all containers
    measurements = page.evaluate("""() => {
        const viewport = {
            width: window.innerWidth,
            height: window.innerHeight
        };
        
        const body = document.body;
        const headerSection = document.querySelector('.header-section');
        const board = document.querySelector('.board');
        const boardGrid = document.querySelector('.board-grid');
        const keyboard = document.querySelector('.keyboard');
        
        function getBBox(element, name) {
            if (!element) return { name, exists: false };
            const rect = element.getBoundingClientRect();
            return {
                name,
                exists: true,
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height,
                right: rect.right,
                bottom: rect.bottom
            };
        }
        
        return {
            viewport,
            body: getBBox(body, 'body'),
            headerSection: getBBox(headerSection, 'header-section'),
            board: getBBox(board, 'board'),
            boardGrid: getBBox(boardGrid, 'board-grid'),
            keyboard: getBBox(keyboard, 'keyboard')
        };
    }""")
    
    # Check for overlaps
    overlaps = []
    
    def check_overlap(container1, container2):
        """Check if two containers overlap."""
        if not (container1['exists'] and container2['exists']):
            return None
        
        # Containers overlap if they intersect in both X and Y axes
        x_overlap = not (container1['right'] <= container2['x'] or 
                        container2['right'] <= container1['x'])
        y_overlap = not (container1['bottom'] <= container2['y'] or 
                        container2['bottom'] <= container1['y'])
        
        if x_overlap and y_overlap:
            # Calculate overlap area
            x_start = max(container1['x'], container2['x'])
            x_end = min(container1['right'], container2['right'])
            y_start = max(container1['y'], container2['y'])
            y_end = min(container1['bottom'], container2['bottom'])
            
            overlap_width = x_end - x_start
            overlap_height = y_end - y_start
            overlap_area = overlap_width * overlap_height
            
            return {
                'container1': container1['name'],
                'container2': container2['name'],
                'overlap_width': overlap_width,
                'overlap_height': overlap_height,
                'overlap_area': overlap_area
            }
        return None
    
    # Check all container pairs for overlap
    containers = [
        measurements['headerSection'],
        measurements['board'],
        measurements['keyboard']
    ]
    
    for i, c1 in enumerate(containers):
        for c2 in containers[i+1:]:
            overlap = check_overlap(c1, c2)
            if overlap:
                overlaps.append(overlap)
    
    # Also check if board-grid overflows board container
    board = measurements['board']
    board_grid = measurements['boardGrid']
    if board['exists'] and board_grid['exists']:
        # Check if grid extends beyond board boundaries
        overflows = []
        if board_grid['x'] < board['x']:
            overflows.append(f"left by {board['x'] - board_grid['x']:.1f}px")
        if board_grid['y'] < board['y']:
            overflows.append(f"top by {board['y'] - board_grid['y']:.1f}px")
        if board_grid['right'] > board['right']:
            overflows.append(f"right by {board_grid['right'] - board['right']:.1f}px")
        if board_grid['bottom'] > board['bottom']:
            overflows.append(f"bottom by {board_grid['bottom'] - board['bottom']:.1f}px")
        
        if overflows:
            overlaps.append({
                'container1': 'board-grid',
                'container2': 'board (parent)',
                'overflow': ', '.join(overflows),
                'note': 'Grid overflows its parent container'
            })
    
    result = {
        'test_name': test_name,
        'passed': len(overlaps) == 0,
        'overlaps': overlaps,
        'measurements': measurements
    }
    
    return result


def test_wordle_containers_phone_6x3(page, static_dir):
    """Test container overlap on phone layout with 6×3 grid.
    
    The 'page' parameter is a Playwright fixture provided by pytest-playwright.
    Tests the actual production HTML and CSS from src/static/.
    """
    # Phone viewport
    page.set_viewport_size({"width": 400, "height": 844})
    
    # Navigate to production HTML file
    html_path = static_dir / "index.html"
    page.goto(f"file://{html_path}")
    
    # Remove the broken CSS link and inject production CSS content
    css_path = static_dir / "style.css"
    css_content = css_path.read_text()
    
    page.evaluate("""() => {
        // Remove existing stylesheet link (points to /static/style.css which doesn't work with file://)
        const existingLinks = document.querySelectorAll('link[rel="stylesheet"]');
        existingLinks.forEach(link => link.remove());
    }""")
    
    page.add_style_tag(content=css_content)
    page.wait_for_timeout(500)
    
    # Initialize grid with 6x3 configuration
    page.evaluate("""() => {
        document.documentElement.style.setProperty('--cols', '3');
        document.documentElement.style.setProperty('--rows', '6');
        
        const board = document.getElementById('game-board');
        board.innerHTML = '';
        
        const gridContainer = document.createElement('div');
        gridContainer.className = 'board-grid';
        
        for (let i = 0; i < 6; i++) {
            for (let j = 0; j < 3; j++) {
                const tile = document.createElement('div');
                tile.className = 'tile';
                tile.dataset.row = i;
                tile.dataset.col = j;
                gridContainer.appendChild(tile);
            }
        }
        
        board.appendChild(gridContainer);
    }""")
    
    page.wait_for_timeout(500)
    
    # Check for overlaps
    result = check_containers_not_overlapping(page, "Phone 6×3")
    
    # Check if tiles are square
    square_result = check_tiles_are_square(page, "Phone 6×3", tolerance_px=1)
    
    # Print results
    print(f"\n{'='*60}")
    print(f"Test: {result['test_name']}")
    print(f"Viewport: {result['measurements']['viewport']['width']}×{result['measurements']['viewport']['height']}")
    print(f"Overlap Status: {'✓ PASS' if result['passed'] else '✗ FAIL'}")
    print(f"Square Tiles Status: {'✓ PASS' if square_result['passed'] else '✗ FAIL'}")
    
    if result['overlaps']:
        print(f"\nOverlaps detected ({len(result['overlaps'])}):")
        for overlap in result['overlaps']:
            if 'overflow' in overlap:
                print(f"  - {overlap['container1']} overflows {overlap['container2']}: {overlap['overflow']}")
            else:
                print(f"  - {overlap['container1']} overlaps {overlap['container2']}: "
                      f"{overlap['overlap_width']:.1f}×{overlap['overlap_height']:.1f}px "
                      f"(area: {overlap['overlap_area']:.1f}px²)")
    else:
        print("\nNo overlaps detected ✓")
    
    if square_result['non_square_tiles']:
        print(f"\nNon-square tiles detected ({len(square_result['non_square_tiles'])} out of {square_result['tile_count']}):")
        for tile in square_result['non_square_tiles'][:5]:  # Show first 5
            print(f"  - Tile[{tile['row']},{tile['col']}]: {tile['width']:.1f}×{tile['height']:.1f}px "
                  f"(diff: {tile['difference']:.1f}px, ratio: {tile['aspect_ratio']:.3f})")
        if len(square_result['non_square_tiles']) > 5:
            print(f"  ... and {len(square_result['non_square_tiles']) - 5} more")
    else:
        print(f"\nAll {square_result['tile_count']} tiles are square ✓")
    
    print(f"{'='*60}\n")
    
    # Assert no overlaps (this should pass on phone)
    assert result['passed'], f"Containers overlap on phone 6×3 layout: {result['overlaps']}"
    
    # Assert tiles are square (this should pass on phone)
    assert square_result['passed'], f"Tiles are not square on phone 6×3 layout: {len(square_result['non_square_tiles'])} tiles have width != height"


def test_wordle_containers_phone_6x25(page, static_dir):
    """Test container overlap on phone layout with 6×25 grid.
    
    The 'page' parameter is a Playwright fixture provided by pytest-playwright.
    Tests the actual production HTML and CSS from src/static/.
    """
    # Phone viewport
    page.set_viewport_size({"width": 400, "height": 844})
    
    # Navigate to production HTML file
    html_path = static_dir / "index.html"
    page.goto(f"file://{html_path}")
    
    # Remove the broken CSS link and inject production CSS content
    css_path = static_dir / "style.css"
    css_content = css_path.read_text()
    
    page.evaluate("""() => {
        const existingLinks = document.querySelectorAll('link[rel="stylesheet"]');
        existingLinks.forEach(link => link.remove());
    }""")
    
    page.add_style_tag(content=css_content)
    page.wait_for_timeout(500)
    
    # Initialize grid with 6x25 configuration
    page.evaluate("""() => {
        document.documentElement.style.setProperty('--cols', '25');
        document.documentElement.style.setProperty('--rows', '6');
        
        const board = document.getElementById('game-board');
        board.innerHTML = '';
        
        const gridContainer = document.createElement('div');
        gridContainer.className = 'board-grid';
        
        for (let i = 0; i < 6; i++) {
            for (let j = 0; j < 25; j++) {
                const tile = document.createElement('div');
                tile.className = 'tile';
                tile.dataset.row = i;
                tile.dataset.col = j;
                gridContainer.appendChild(tile);
            }
        }
        
        board.appendChild(gridContainer);
    }""")
    
    page.wait_for_timeout(500)
    
    # Check for overlaps
    result = check_containers_not_overlapping(page, "Phone 6×25")
    
    # Check if tiles are square
    square_result = check_tiles_are_square(page, "Phone 6×25", tolerance_px=1)
    
    # Print results
    print(f"\n{'='*60}")
    print(f"Test: {result['test_name']}")
    print(f"Viewport: {result['measurements']['viewport']['width']}×{result['measurements']['viewport']['height']}")
    print(f"Overlap Status: {'✓ PASS' if result['passed'] else '✗ FAIL'}")
    print(f"Square Tiles Status: {'✓ PASS' if square_result['passed'] else '✗ FAIL'}")
    
    if result['overlaps']:
        print(f"\nOverlaps detected ({len(result['overlaps'])}):")
        for overlap in result['overlaps']:
            if 'overflow' in overlap:
                print(f"  - {overlap['container1']} overflows {overlap['container2']}: {overlap['overflow']}")
            else:
                print(f"  - {overlap['container1']} overlaps {overlap['container2']}: "
                      f"{overlap['overlap_width']:.1f}×{overlap['overlap_height']:.1f}px "
                      f"(area: {overlap['overlap_area']:.1f}px²)")
    else:
        print("\nNo overlaps detected ✓")
    
    if square_result['non_square_tiles']:
        print(f"\nNon-square tiles detected ({len(square_result['non_square_tiles'])} out of {square_result['tile_count']}):")
        for tile in square_result['non_square_tiles'][:5]:  # Show first 5
            print(f"  - Tile[{tile['row']},{tile['col']}]: {tile['width']:.1f}×{tile['height']:.1f}px "
                  f"(diff: {tile['difference']:.1f}px, ratio: {tile['aspect_ratio']:.3f})")
        if len(square_result['non_square_tiles']) > 5:
            print(f"  ... and {len(square_result['non_square_tiles']) - 5} more")
    else:
        print(f"\nAll {square_result['tile_count']} tiles are square ✓")
    
    print(f"{'='*60}\n")
    
    # Assert no overlaps (this should pass on phone)
    assert result['passed'], f"Containers overlap on phone 6×25 layout: {result['overlaps']}"
    
    # Assert tiles are square (this should pass on phone)
    assert square_result['passed'], f"Tiles are not square on phone 6×25 layout: {len(square_result['non_square_tiles'])} tiles have width != height"


def test_wordle_containers_desktop_6x3(page, static_dir):
    """Test container overlap on desktop layout with 6×3 grid.
    
    The 'page' parameter is a Playwright fixture provided by pytest-playwright.
    This test currently fails due to grid overflow - will be fixed in future commits.
    Tests the actual production HTML and CSS from src/static/.
    """
    # Desktop viewport
    page.set_viewport_size({"width": 1280, "height": 720})
    
    # Navigate to production HTML file
    html_path = static_dir / "index.html"
    page.goto(f"file://{html_path}")
    
    # Remove the broken CSS link and inject production CSS content
    css_path = static_dir / "style.css"
    css_content = css_path.read_text()
    
    page.evaluate("""() => {
        const existingLinks = document.querySelectorAll('link[rel="stylesheet"]');
        existingLinks.forEach(link => link.remove());
    }""")
    
    page.add_style_tag(content=css_content)
    page.wait_for_timeout(500)
    
    # Initialize grid with 6x3 configuration
    page.evaluate("""() => {
        document.documentElement.style.setProperty('--cols', '3');
        document.documentElement.style.setProperty('--rows', '6');
        
        const board = document.getElementById('game-board');
        board.innerHTML = '';
        
        const gridContainer = document.createElement('div');
        gridContainer.className = 'board-grid';
        
        for (let i = 0; i < 6; i++) {
            for (let j = 0; j < 3; j++) {
                const tile = document.createElement('div');
                tile.className = 'tile';
                tile.dataset.row = i;
                tile.dataset.col = j;
                gridContainer.appendChild(tile);
            }
        }
        
        board.appendChild(gridContainer);
    }""")
    
    page.wait_for_timeout(500)
    
    # Check for overlaps
    result = check_containers_not_overlapping(page, "Desktop 6×3")
    
    # Check if tiles are square
    square_result = check_tiles_are_square(page, "Desktop 6×3", tolerance_px=1)
    
    # Print results
    print(f"\n{'='*60}")
    print(f"Test: {result['test_name']}")
    print(f"Viewport: {result['measurements']['viewport']['width']}×{result['measurements']['viewport']['height']}")
    print(f"Overlap Status: {'✓ PASS' if result['passed'] else '✗ FAIL (EXPECTED)'}")
    print(f"Square Tiles Status: {'✓ PASS' if square_result['passed'] else '✗ FAIL (EXPECTED)'}")
    
    if result['overlaps']:
        print(f"\nOverlaps detected ({len(result['overlaps'])}):")
        for overlap in result['overlaps']:
            if 'overflow' in overlap:
                print(f"  - {overlap['container1']} overflows {overlap['container2']}: {overlap['overflow']}")
            else:
                print(f"  - {overlap['container1']} overlaps {overlap['container2']}: "
                      f"{overlap['overlap_width']:.1f}×{overlap['overlap_height']:.1f}px "
                      f"(area: {overlap['overlap_area']:.1f}px²)")
    else:
        print("\nNo overlaps detected ✓")
    
    if square_result['non_square_tiles']:
        print(f"\nNon-square tiles detected ({len(square_result['non_square_tiles'])} out of {square_result['tile_count']}):")
        for tile in square_result['non_square_tiles'][:5]:  # Show first 5
            print(f"  - Tile[{tile['row']},{tile['col']}]: {tile['width']:.1f}×{tile['height']:.1f}px "
                  f"(diff: {tile['difference']:.1f}px, ratio: {tile['aspect_ratio']:.3f})")
        if len(square_result['non_square_tiles']) > 5:
            print(f"  ... and {len(square_result['non_square_tiles']) - 5} more")
    else:
        print(f"\nAll {square_result['tile_count']} tiles are square ✓")
    
    print(f"{'='*60}\n")
    
    # Assert no overlaps - this test will fail until the issue is fixed
    assert result['passed'], f"Containers overlap on desktop 6×3 layout: {result['overlaps']}"
    
    # Assert tiles are square - this test is expected to fail on desktop
    assert square_result['passed'], f"Tiles are not square on desktop 6×3 layout: {len(square_result['non_square_tiles'])} tiles have width != height"


def test_wordle_containers_desktop_6x25(page, static_dir):
    """Test container overlap on desktop layout with 6×25 grid.
    
    The 'page' parameter is a Playwright fixture provided by pytest-playwright.
    Tests the actual production HTML and CSS from src/static/.
    """
    # Desktop viewport
    page.set_viewport_size({"width": 1280, "height": 720})
    
    # Navigate to production HTML file
    html_path = static_dir / "index.html"
    page.goto(f"file://{html_path}")
    
    # Remove the broken CSS link and inject production CSS content
    css_path = static_dir / "style.css"
    css_content = css_path.read_text()
    
    page.evaluate("""() => {
        const existingLinks = document.querySelectorAll('link[rel="stylesheet"]');
        existingLinks.forEach(link => link.remove());
    }""")
    
    page.add_style_tag(content=css_content)
    page.wait_for_timeout(500)
    
    # Initialize grid with 6x25 configuration
    page.evaluate("""() => {
        document.documentElement.style.setProperty('--cols', '25');
        document.documentElement.style.setProperty('--rows', '6');
        
        const board = document.getElementById('game-board');
        board.innerHTML = '';
        
        const gridContainer = document.createElement('div');
        gridContainer.className = 'board-grid';
        
        for (let i = 0; i < 6; i++) {
            for (let j = 0; j < 25; j++) {
                const tile = document.createElement('div');
                tile.className = 'tile';
                tile.dataset.row = i;
                tile.dataset.col = j;
                gridContainer.appendChild(tile);
            }
        }
        
        board.appendChild(gridContainer);
    }""")
    
    page.wait_for_timeout(500)
    
    # Check for overlaps
    result = check_containers_not_overlapping(page, "Desktop 6×25")
    
    # Check if tiles are square
    square_result = check_tiles_are_square(page, "Desktop 6×25", tolerance_px=1)
    
    # Print results
    print(f"\n{'='*60}")
    print(f"Test: {result['test_name']}")
    print(f"Viewport: {result['measurements']['viewport']['width']}×{result['measurements']['viewport']['height']}")
    print(f"Overlap Status: {'✓ PASS' if result['passed'] else '✗ FAIL (EXPECTED)'}")
    print(f"Square Tiles Status: {'✓ PASS' if square_result['passed'] else '✗ FAIL (EXPECTED)'}")
    
    if result['overlaps']:
        print(f"\nOverlaps detected ({len(result['overlaps'])}):")
        for overlap in result['overlaps']:
            if 'overflow' in overlap:
                print(f"  - {overlap['container1']} overflows {overlap['container2']}: {overlap['overflow']}")
            else:
                print(f"  - {overlap['container1']} overlaps {overlap['container2']}: "
                      f"{overlap['overlap_width']:.1f}×{overlap['overlap_height']:.1f}px "
                      f"(area: {overlap['overlap_area']:.1f}px²)")
    else:
        print("\nNo overlaps detected ✓")
    
    if square_result['non_square_tiles']:
        print(f"\nNon-square tiles detected ({len(square_result['non_square_tiles'])} out of {square_result['tile_count']}):")
        for tile in square_result['non_square_tiles'][:5]:  # Show first 5
            print(f"  - Tile[{tile['row']},{tile['col']}]: {tile['width']:.1f}×{tile['height']:.1f}px "
                  f"(diff: {tile['difference']:.1f}px, ratio: {tile['aspect_ratio']:.3f})")
        if len(square_result['non_square_tiles']) > 5:
            print(f"  ... and {len(square_result['non_square_tiles']) - 5} more")
    else:
        print(f"\nAll {square_result['tile_count']} tiles are square ✓")
    
    print(f"{'='*60}\n")
    
    # Assert no overlaps (this should pass)
    assert result['passed'], f"Containers overlap on desktop 6×25 layout: {result['overlaps']}"
    
    # Assert tiles are square - this test is expected to fail on desktop
    assert square_result['passed'], f"Tiles are not square on desktop 6×25 layout: {len(square_result['non_square_tiles'])} tiles have width != height"
