# HTML/CSS Layout Testing with Playwright - Step 1 Summary

## Overview
This document describes the completion of Step 1: Installing and configuring Playwright for HTML/CSS layout testing in the Riddle repository.

## What Was Added

### 1. Dependencies (pyproject.toml)
- Added `playwright>=1.49.0` to dev dependencies
- Added `pytest-playwright>=0.7.0` to dev dependencies
- These integrate Playwright with the existing pytest framework

### 2. Playwright Configuration (playwright.config.py)
- Created a minimal configuration file at the repository root
- Configured default viewport size: 1280x720
- Uses pytest-playwright plugin for seamless integration with existing test infrastructure

### 3. Test Structure
Created `tests/playwright/` directory containing:

#### test_page.html
- A minimal HTML page for smoke testing
- Simple centered layout with flexbox
- Demonstrates that Playwright can load local HTML files
- No external dependencies (pure HTML/CSS)

#### test_smoke.py
- Two smoke tests to verify Playwright functionality:
  1. `test_playwright_smoke`: Loads the test HTML page, verifies page title, DOM querying, and text content reading
  2. `test_browser_basic_functionality`: Tests navigation to about:blank, JavaScript evaluation, and content injection
- Tests use Chromium browser by default (via pytest-playwright's automatic browser parameterization)
- Includes screenshot capture for visual verification

### 4. CI Integration (.github/workflows/ci.yml)
- Added step to install Playwright browsers (chromium only for efficiency)
- Playwright tests run as part of the main pytest suite
- No separate workflow needed - integrated with existing CI

### 5. Artifact Management (.gitignore)
- Added exclusions for Playwright test artifacts:
  - `tests/playwright/*.png` (screenshots)
  - `tests/playwright/test-results/` (test output)
  - `.playwright/` (cache directory)

## What Worked

✅ **Dependency Installation**: `uv sync` successfully installed Playwright and pytest-playwright  
✅ **Browser Installation**: `uv run playwright install chromium` downloaded Chromium successfully  
✅ **Local Testing**: Both smoke tests pass locally in ~1.7 seconds  
✅ **Screenshot Capture**: Playwright successfully captures screenshots of rendered pages  
✅ **pytest Integration**: pytest-playwright integrates seamlessly with existing test infrastructure  
✅ **Minimal Configuration**: Simple config file with just viewport settings works perfectly  

## What Did Not Work / Issues Encountered

⚠️ **UV Installation**: The `uv` command was not pre-installed in the environment. Had to install it via `pip3 install uv` before proceeding. This shouldn't be an issue in CI since the workflow uses `astral-sh/setup-uv@v4` action.

## Important Decisions & Design Choices

### 1. Browser Choice
- **Decision**: Install only Chromium browser
- **Rationale**: Chromium is sufficient for layout testing, faster CI runs, and covers the majority of modern web standards
- **Future**: Can add Firefox/WebKit later if cross-browser testing becomes necessary

### 2. Test Organization
- **Decision**: Created `tests/playwright/` subdirectory within existing `tests/` structure
- **Rationale**: Keeps Playwright tests separate from Python unit tests while maintaining discoverability
- **Future**: All HTML/CSS layout tests should go in this directory

### 3. Configuration Approach
- **Decision**: Minimal Python-based configuration instead of full playwright.config.ts
- **Rationale**: Python project, simpler integration with pytest, follows existing patterns
- **Future**: Can extend with more fixtures if needed

### 4. Integration with Existing Tests
- **Decision**: Playwright tests run as part of main pytest suite (not a separate workflow)
- **Rationale**: Simpler CI, all tests in one place, consistent reporting
- **Future**: If Playwright tests become slow, consider separating them

### 5. Test Scope
- **Decision**: Created minimal smoke tests only (no layout assertions yet)
- **Rationale**: Following Step 1 requirements explicitly - just prove Playwright works
- **Future**: Steps 2-4 will add actual layout testing capabilities

## Warnings for Next Steps

### Critical Constraints
1. **Do NOT modify application code**: The existing Wordle game in `src/static/` should not be touched until Step 4
2. **Keep tests isolated**: Create separate HTML files for testing, don't reuse `src/static/index.html` yet
3. **Browser availability**: CI installs Chromium only - tests using other browsers will fail

### Technical Considerations
1. **File URLs**: The smoke test uses `file://` URLs which work fine locally and in CI
   - Future tests may need a local HTTP server for more realistic testing
   - Consider using pytest-playwright's `page.goto()` with a test server fixture if needed

2. **Screenshot Storage**: Screenshots are currently saved in `tests/playwright/` and gitignored
   - If you need to store reference screenshots for visual regression testing, use a different location
   - Consider using Playwright's built-in screenshot comparison features

3. **Viewport Size**: Default is 1280x720
   - Adequate for desktop testing
   - Mobile testing will require responsive viewport configurations
   - The existing Wordle game uses modern viewport units (dvh) that should be tested with various sizes

4. **Async vs Sync**: Current tests use sync API (`page.goto()`)
   - This is fine for simple tests
   - Complex interactions may benefit from async API
   - pytest-playwright supports both styles

### Known Limitations
1. **No test server yet**: Tests load static HTML files directly
   - Good enough for Steps 2-3
   - Step 4 may need the actual FastAPI server running for realistic testing

2. **No visual regression testing**: Just smoke tests for now
   - Future steps should add screenshot comparison
   - Consider tools like `playwright-pytest` assertions or pixelmatch

3. **Single browser only**: Chromium is sufficient for layout work
   - Cross-browser testing can be added later if needed
   - The existing instructions mention CSS features (aspect-ratio, container queries, dvh units) that are well-supported in modern Chromium

## Next Steps (For Future Agents)

### Step 2: Minimal HTML+CSS with Unit Test
- Create a trivial test case (e.g., a single colored box with specific dimensions)
- Write tests that assert computed styles, dimensions, positions
- Validate that Playwright can accurately measure layout properties

### Step 3: Flexbox Container Tests
- Create HTML with flexbox containers (similar to the Wordle game structure)
- Test flex properties, alignment, spacing
- Validate responsive behavior with different viewport sizes

### Step 4: Complex Layout Testing
- Test the actual Wordle game layout from `src/static/`
- Validate the CSS Grid with dynamic aspect-ratio
- Test various grid configurations (6x3, 6x5, 6x25)
- Verify square tiles, responsive font sizing, proper centering
- Test on multiple viewport sizes (mobile, tablet, desktop)
- Reference the architecture docs in `.github/instructions/static_wordle_architecture.instructions.md`

## Testing Commands

```bash
# Run all tests including Playwright
uv run pytest tests

# Run only Playwright tests
uv run pytest tests/playwright

# Run with verbose output
uv run pytest tests/playwright -v

# Run specific test
uv run pytest tests/playwright/test_smoke.py::test_playwright_smoke -v
```

## Verification

The setup is working correctly when:
- ✅ `uv sync` installs dependencies without errors
- ✅ `uv run playwright install chromium` completes successfully
- ✅ `uv run pytest tests/playwright -v` shows all tests passing
- ✅ Screenshot file is created at `tests/playwright/smoke_test_screenshot.png`
- ✅ CI workflow passes with Playwright tests included

## Resources

- [Playwright Python Documentation](https://playwright.dev/python/docs/intro)
- [pytest-playwright Plugin](https://github.com/microsoft/playwright-pytest)
- [Wordle Layout Architecture](.github/instructions/static_wordle_architecture.instructions.md)
