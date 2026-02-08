"""Debug script to show exact container measurements for desktop 6x3 configuration."""

from playwright.sync_api import sync_playwright
from pathlib import Path

static_dir = Path(__file__).parent.parent / "src" / "static"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    
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
    
    # Get all measurements
    measurements = page.evaluate("""() => {
        const viewport = {
            width: window.innerWidth,
            height: window.innerHeight
        };
        
        function getBBox(element, name) {
            if (!element) return { name, exists: false };
            const rect = element.getBoundingClientRect();
            const computed = window.getComputedStyle(element);
            return {
                name,
                exists: true,
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height,
                right: rect.right,
                bottom: rect.bottom,
                computedWidth: computed.width,
                computedHeight: computed.height,
                display: computed.display,
                position: computed.position,
                flexGrow: computed.flexGrow,
                flexShrink: computed.flexShrink,
                flexBasis: computed.flexBasis
            };
        }
        
        return {
            viewport,
            body: getBBox(document.body, 'body'),
            container: getBBox(document.querySelector('.container'), 'container'),
            headerSection: getBBox(document.querySelector('.header-section'), 'header-section'),
            board: getBBox(document.querySelector('.board'), 'board'),
            boardGrid: getBBox(document.querySelector('.board-grid'), 'board-grid'),
            keyboard: getBBox(document.querySelector('.keyboard'), 'keyboard')
        };
    }""")
    
    # Print detailed measurements
    print("\n" + "="*80)
    print("DESKTOP 6×3 LAYOUT - DETAILED MEASUREMENTS")
    print("="*80)
    print(f"\nViewport: {measurements['viewport']['width']}×{measurements['viewport']['height']}")
    
    for name in ['body', 'container', 'headerSection', 'board', 'boardGrid', 'keyboard']:
        container = measurements[name]
        if container['exists']:
            print(f"\n{container['name'].upper()}:")
            print(f"  Position: x={container['x']:.1f}, y={container['y']:.1f}")
            print(f"  Size: {container['width']:.1f}×{container['height']:.1f}")
            print(f"  Right edge: {container['right']:.1f}, Bottom edge: {container['bottom']:.1f}")
            print(f"  Computed size: {container['computedWidth']} × {container['computedHeight']}")
            print(f"  Display: {container['display']}, Position: {container['position']}")
            if container['flexGrow'] or container['flexShrink'] != '1' or container['flexBasis'] != 'auto':
                print(f"  Flex: grow={container['flexGrow']}, shrink={container['flexShrink']}, basis={container['flexBasis']}")
    
    # Check for overlaps
    print("\n" + "="*80)
    print("OVERLAP ANALYSIS")
    print("="*80)
    
    # Check if board-grid overlaps header-section
    grid = measurements['boardGrid']
    header = measurements['headerSection']
    if grid['exists'] and header['exists']:
        if grid['y'] < header['bottom']:
            overlap_height = header['bottom'] - grid['y']
            print(f"\n⚠️  OVERLAP DETECTED: board-grid overlaps header-section")
            print(f"   Header bottom: {header['bottom']:.1f}px")
            print(f"   Grid top: {grid['y']:.1f}px")
            print(f"   Overlap: {overlap_height:.1f}px")
        else:
            gap = grid['y'] - header['bottom']
            print(f"\n✓ No overlap: board-grid and header-section have {gap:.1f}px gap")
    
    # Check if board-grid overlaps keyboard
    keyboard = measurements['keyboard']
    if grid['exists'] and keyboard['exists']:
        if grid['bottom'] > keyboard['y']:
            overlap_height = grid['bottom'] - keyboard['y']
            print(f"\n⚠️  OVERLAP DETECTED: board-grid overlaps keyboard")
            print(f"   Grid bottom: {grid['bottom']:.1f}px")
            print(f"   Keyboard top: {keyboard['y']:.1f}px")
            print(f"   Overlap: {overlap_height:.1f}px")
        else:
            gap = keyboard['y'] - grid['bottom']
            print(f"\n✓ No overlap: board-grid and keyboard have {gap:.1f}px gap")
    
    # Check if board-grid overflows board container
    board = measurements['board']
    if grid['exists'] and board['exists']:
        print(f"\n{'='*80}")
        print("BOARD-GRID vs BOARD CONTAINER")
        print("="*80)
        
        overflows = []
        if grid['y'] < board['y']:
            overflows.append(f"top by {board['y'] - grid['y']:.1f}px")
        if grid['bottom'] > board['bottom']:
            overflows.append(f"bottom by {grid['bottom'] - board['bottom']:.1f}px")
        if grid['x'] < board['x']:
            overflows.append(f"left by {board['x'] - grid['x']:.1f}px")
        if grid['right'] > board['right']:
            overflows.append(f"right by {grid['right'] - board['right']:.1f}px")
        
        if overflows:
            print(f"\n⚠️  OVERFLOW DETECTED: board-grid overflows board container")
            for overflow in overflows:
                print(f"   - {overflow}")
        else:
            print(f"\n✓ No overflow: board-grid stays within board container")
    
    print("\n" + "="*80 + "\n")
    
    browser.close()
