"""Riddle common module - shared code for word games."""

from .common import *
from .game_state import *
from .riddle_game import RiddleGame
from .similarity_matrix_codec import *

def repo_root_path() -> Path:
    """Get the root path of the riddle repo."""
    repo_root = Path(__file__).parent
    while not (repo_root / ".git").exists():
        repo_root = repo_root.parent
    return repo_root

REPO_ROOT_PATH: Path = repo_root_path()
    

__all__ = ['RiddleGame']
