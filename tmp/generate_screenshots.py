"""Generate screenshots of Wordle layout for different grid configurations and viewports."""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

# Add parent directory to path to use the test fixture logic
sys.path.insert(0, str(Path(__file__).parent.parent))

def generate_screenshots():
    """Generate screenshots for 6x3 and 6x25 grids on mobile and desktop."""
    
    static_dir = Path(__file__).parent.parent / "src" / "static"
    html_path = static_dir / "index.html"
    css_path = static_dir / "style.css"
    
    # Read the CSS content
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
            
            # Load the HTML file
            page.goto(f"file://{html_path.absolute()}")
            
            # Remove the broken stylesheet link
            page.evaluate("""
                () => {
                    const link = document.querySelector('link[href="/static/style.css"]');
                    if (link) link.remove();
                }
            """)
            
            # Inject the actual production CSS
            page.add_style_tag(content=css_content)
            
            # Wait for page to be ready
            page.wait_for_load_state("networkidle")
            
            # Initialize the grid and keyboard with the desired configuration
            page.evaluate(f"""
                () => {{
                    // Set CSS variables for grid size
                    document.documentElement.style.setProperty('--cols', '{cols}');
                    document.documentElement.style.setProperty('--rows', '{rows}');
                    
                    // Create tiles in the grid
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
                    
                    // Create keyboard
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
            
            # Wait a moment for rendering
            page.wait_for_timeout(500)
            
            # Take screenshot
            screenshot_path = Path(__file__).parent / f"{viewport_name}_{grid_name}.png"
            page.screenshot(path=str(screenshot_path))
            print(f"  Saved: {screenshot_path}")
            
            page.close()
        
        browser.close()
    
    print("\nAll screenshots generated successfully!")

if __name__ == "__main__":
    generate_screenshots()
