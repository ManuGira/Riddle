import enum
import dataclasses
from abc import abstractmethod, ABC
from typing import Callable, Any, TypeVar, Generic


class Language(enum.StrEnum):
    FR = "FR"
    EN = "EN"


class GameState(ABC):
    """
    Abstract base class for game state.

    All game states must be serializable to/from dict for JWT storage.
    """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """
        Convert state to dictionary for JWT encoding.

        Returns:
            Dictionary representation of the state
        """
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> 'GameState':
        """
        Reconstruct state from dictionary (from JWT).

        Args:
            data: Dictionary representation of the state

        Returns:
            GameState instance
        """
        pass

    @abstractmethod
    def is_game_over(self) -> bool:
        """
        Check if the game is over.

        Returns:
            True if game is over (won or lost)
        """
        pass


class RiddleGame(ABC):
    """
    Interface for Wordle-like games.

    Each instance represents ONE game for ONE specific date.
    The server will cache multiple instances (one per date).

    Each game instance stores its own secret and handles guess checking.
    No need for date-based caching - that's the server's responsibility.
    """

    def __init__(self, date_str: str):
        """
        Initialize the game instance for a specific date.

        Args:
            date_str: The date for this game instance in format "YYYY-MM-DD"
        """
        self._date = date_str
        self._secret = self._generate_challenge(date_str)

    @abstractmethod
    def _generate_challenge(self, date_str: str) -> str:
        """
        Generate the challenge/secret for a given date.

        Args:
            date_str: Date in format "YYYY-MM-DD"

        Returns:
            The generated secret word/challenge

        Note:
            Must be deterministic - same date must always return same secret.
            This is called once during __init__ to create the secret.
        """
        raise NotImplementedError("_generate_challenge must be implemented by subclass")

    @property
    def secret(self) -> str:
        """Get the secret for this game instance."""
        return self._secret

    @property
    def date(self) -> str:
        """Get the date for this game instance."""
        return self._date

    @abstractmethod
    def create_game_state(self) -> GameState:
        """
        Create a new initial game state.

        Returns:
            New GameState instance for this game
        """
        raise NotImplementedError("create_game_state must be implemented by subclass")

    @abstractmethod
    def check_guess(self, guess: str, game_state: GameState | None = None) -> GameState:
        """
        Process a guess and return hints/feedback.

        Uses the secret stored in self._secret (set during __init__).

        Args:
            guess: The player's guess

        Returns:
            Dictionary containing:
                - "guess": The processed guess (normalized)
                - "hints": List of hint objects (format depends on game)
                - "is_correct": Boolean indicating if guess matches secret

        Example for Wordle:
            {
                "guess": "CRANE",
                "hints": [
                    {"letter": "C", "status": "absent"},
                    {"letter": "R", "status": "present"},
                    ...
                ],
                "is_correct": False
            }
        """
        raise NotImplementedError("check_guess must be implemented by subclass")


GameT = TypeVar('GameT', bound='RiddleGame')

@dataclasses.dataclass()
class GameFactory(Generic[GameT]):
    url: str
    create_game_instance: Callable[[str], GameT]  # Function that takes date_str and returns a game instance

