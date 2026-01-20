

from wordle.wordle_game import WordleGame
from riddle.types import Language, GameFactory
from riddle import DATA_FOLDER_PATH
from pathlib import Path

def get_wordle_word_list_filepath(language: Language, word_length: int) -> Path:
    words_list_dirpath = DATA_FOLDER_PATH / "words_lists"
    return words_list_dirpath / f"wordle_list_{language}_L{word_length}_base.txt"

def generate_wordle_factory(language: Language, word_length: int, secret_key: str) -> GameFactory[WordleGame]:
    """
    Generate a Wordle game factory for the given language and word length.
    Args:
        language (Language): Language of the word list.
        word_length (int): Length of the words.
        secret_key (str): Secret key for the game.
    Returns:
        GameFactory: A dataclass containing the URL slug and factory function.
    """

    # Configuration for each game
    words_file: Path = get_wordle_word_list_filepath(language, word_length)
    
    # Create game factory
    def wordle_factory(date_str: str) -> WordleGame:
        return WordleGame(date_str, words_file, secret_key)
    
    # Create URL slug for the game. Typically: "wordle-en-5" or "wordle-fr-6"
    wordle_url_slug = f"wordle-{language.lower()}-{word_length}"

    return GameFactory(wordle_url_slug, wordle_factory)
    
