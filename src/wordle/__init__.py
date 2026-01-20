"""Wordle game implementations."""

# ignore F401: imported but unused
# flake8: noqa: F401

from riddle import Language
from riddle import DATA_FOLDER_PATH
from pathlib import Path

from .factory_generator import generate_wordle_factory, get_wordle_word_list_filepath


def get_lexicon_path(language: Language) -> Path:
    lexicon_path = DATA_FOLDER_PATH / f"OpenLexicon_{language}.tsv"
    return lexicon_path