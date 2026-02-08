"""Generate screenshots of Wordle production layout for different grid configurations.

This script renders the actual production code from src/static/ by:
1. Loading the production HTML (index.html)
2. Injecting the production CSS (style.css)  
3. Manually initializing tiles and keyboard (production game.js needs server API)
4. Capturing screenshots at different viewport sizes
"""

from pathlib import Path
from playwright.sync_api import sync_playwright

def generate_screenshots():
    """Generate screenshots for 6x3 and 6x25 grids on mobile and desktop."""
    
    static_dir = Path(__file__).parent.parent / "src" / "static"
    html_path = static_dir / "index.html"
    css_path = static_dir / "style.css"
    
    # Read the production CSS
    css_content = css_path.read_text()
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        
        configs = [
            # (viewport_name, width, height, grid_name, cols, rows)
            ("mobile", 400, 844, "6x3", 3, 6),
            ("mobile", 400, 844, "6x25", 25, 6),
            ("desktop", 1280, 720, "6x3", 3, 6),
            ("desktop", 1280, 720, "6x25", 25, 6),
        ]
        
        for viewport_name, width, height, grid_name, cols, rows in configs:
            print(f"Generating screenshot: {viewport_name}_{grid_name}...")
            
            page = browser.new_page(viewport={"width": width, "height": height})
            
            # Load the production HTML file
            page.goto(f"file://{html_path.absolute()}")
            
            # Remove the broken stylesheet and script links (won't work with file:// protocol)
            page.evaluate("""
                () => {
                    const link = document.querySelector('link[href="/static/style.css"]');
                    if (link) link.remove();
                    const script = document.querySelector('script[src="/static/game.js"]');
                    if (script) script.remove();
                }
            """)
            
            # Inject the actual production CSS
            page.add_style_tag(content=css_content)
            
            # Wait for page structure to be ready
            page.wait_for_load_state("networkidle")
            
            # Initialize the grid and keyboard to match the configuration
            # Note: Production game.js requires a server API, so we manually populate the UI
            page.evaluate(f"""
                () => {{
                    // Set CSS variables for grid size (used by production CSS)
                    document.documentElement.style.setProperty('--cols', '{cols}');
                    document.documentElement.style.setProperty('--rows', '{rows}');
                    
                    // Create tiles in the grid (same as production game.js would do)
                    const grid = document.querySelector('.board-grid');
                    if (grid) {{
                        grid.innerHTML = '';
                        for (let row = 0; row < {rows}; row++) {{
                            for (let col = 0; col < {cols}; col++) {{
                                const tile = document.createElement('div');
                                tile.className = 'tile';
                                tile.dataset.row = row;
                                tile.dataset.col = col;
                                tile.textContent = '';
                                grid.appendChild(tile);
                            }}
                        }}
                    }}
                    
                    // Create keyboard (same as production game.js would do)
                    const keyboard = document.getElementById('keyboard');
                    const keyboardLayout = [
                        ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
                        ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
                        ['ENTER', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', '⌫']
                    ];
                    
                    if (keyboard) {{
                        keyboard.innerHTML = '';
                        keyboardLayout.forEach(row => {{
                            const keyRow = document.createElement('div');
                            keyRow.className = 'keyboard-row';
                            
                            row.forEach(key => {{
                                const button = document.createElement('button');
                                button.className = 'key';
                                
                                if (key === 'ENTER') {{
                                    button.classList.add('key-large');
                                    button.textContent = 'ENTER';
                                }} else if (key === '⌫') {{
                                    button.classList.add('key-large');
                                    button.textContent = '⌫';
                                }} else {{
                                    button.textContent = key;
                                    button.dataset.letter = key;
                                }}
                                
                                keyRow.appendChild(button);
                            }});
                            
                            keyboard.appendChild(keyRow);
                        }});
                    }}
                }}
            """)
            
            # Wait a moment for complete rendering
            page.wait_for_timeout(500)
            
            # Take screenshot
            screenshot_path = Path(__file__).parent / f"{viewport_name}_{grid_name}.png"
            page.screenshot(path=str(screenshot_path))
            print(f"  Saved: {screenshot_path}")
            
            page.close()
        
        browser.close()
    
    print("\nAll screenshots generated successfully!")
    print("\nThe screenshots show the production Wordle UI:")
    print("- Production HTML structure from src/static/index.html")
    print("- Production CSS styles from src/static/style.css")
    print("- UI elements initialized to match production game.js behavior")
    print("  (game.js requires server API, so tiles/keyboard are manually populated)")

if __name__ == "__main__":
    generate_screenshots()
