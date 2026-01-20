"""Riddle common module - shared code for word games."""

# ignore F401: imported but unused
# flake8: noqa: F401

from . import common
from .common import REPO_ROOT_PATH, DATA_FOLDER_PATH, STATIC_FOLDER_PATH

from . import types
from .types import Language, GameState, RiddleGame, GameFactory

from . import game_server  # allow "import riddle.game_server"
from .game_server import GameServer  # allow "from riddle.game_server import GameServer"

from . import similarity_matrix_codec

from . import lexicon_parser
from .lexicon_parser import LexiconFR, LexiconEN, Grammar

# Deactivate `from riddle import *` behavior
__all__ = []
