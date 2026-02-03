# Running Python Scripts with UV

This project uses **`uv`** to manage Python scripts instead of the traditional `python` command.

## Usage

To run any Python script in this project, use:

```bash
uv run myscript.py
```

**NOT:**
```bash
python myscript.py
```
# Running CI with UV

Testing, format checking and types checking can all be run at once with powershell file  `./ci.ps1`. 
Alternatively it is possible to run this checks individually

## Testing

tests are also run using `uv`.
To run all tests at once, use:
```bash
uv run pytest tests
```

run individual test files like so:
```bash
uv run pytest tests/test_example.py

```

## Format checking

```bash
uv run ruff --fix .
```

The fix option will automatically apply safe fixes to your code


## Type checking

type checking is currently not working on all files. For now we run them only in folders `src/riddle/` and `src/wordle/`
```bash
uv run ty check ./src/riddle/
uv run ty check ./src/wordle/
```

## Examples

- `uv run src/main_semantic_game.py`
- `uv run src/main_assistant.py`
- `uv run src/main_cluster.py`

For any automation or AI agent execution, always use the `uv run` command format.


## Python Typing Style

When using type hints, **prefer the built-in collection types** (`list`, `dict`, `tuple`, etc.) over importing from `typing` (e.g., avoid `from typing import List, Dict, Tuple`).
Use `list[str]`, `dict[str, int]`, etc., for type annotations.
