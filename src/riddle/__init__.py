"""Riddle common module - shared code for word games."""

from .common import *
from .game_state import *
from .riddle_game import RiddleGame
from .similarity_matrix_codec import *

def repo_root_path() -> Path:
    """Get the root path of the riddle repo."""
    repo_root = Path(__file__).parent
    # Look for pyproject.toml
    while not (repo_root / "pyproject.toml").exists():
        repo_root = repo_root.parent
        # Safety: stop at filesystem root
        if repo_root == repo_root.parent:
            # Fallback: assume we're in src/riddle, so go up 2 levels
            return Path(__file__).parent.parent.parent
    return repo_root

REPO_ROOT_PATH: Path = repo_root_path()
DATA_FOLDER_PATH: Path = REPO_ROOT_PATH / "data"
STATIC_FOLDER_PATH: Path = REPO_ROOT_PATH / "src" / "static"

__all__ = ['RiddleGame']
