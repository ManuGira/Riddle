from abc import ABC, abstractmethod
from typing import Any


class IGamle(ABC):
    """
    Interface for Wordle-like games.
    
    Any game implementation must inherit from this interface and implement
    all abstract methods. This ensures compatibility with the server_game.py
    stateless architecture.
    
    The instance should cache the daily challenge internally to avoid
    expensive regeneration on every guess.
    """
    
    def __init__(self):
        """Initialize the game instance with internal challenge cache."""
        self._challenge_cache: dict[str, str] = {}
    
    def get_daily_challenge(self, date_str: str) -> str:
        """
        Get the daily challenge/secret for a given date (with internal caching).
        
        Args:
            date_str: Date in format "YYYY-MM-DD"
            
        Returns:
            The secret word/challenge for that date
            
        Note:
            Must be deterministic - same date must always return same challenge
            for all players. Challenge is cached internally to avoid regeneration.
        """
        if date_str not in self._challenge_cache:
            self._challenge_cache[date_str] = self._generate_challenge(date_str)
            
            # Prevent memory leak: keep only last 7 days
            if len(self._challenge_cache) > 7:
                oldest_date = min(self._challenge_cache.keys())
                del self._challenge_cache[oldest_date]
        
        return self._challenge_cache[date_str]
    
    @abstractmethod
    def _generate_challenge(self, date_str: str) -> str:
        """
        Internal method to generate a new challenge for a given date.
        
        Args:
            date_str: Date in format "YYYY-MM-DD"
            
        Returns:
            The generated secret word/challenge
            
        Note:
            This is called only once per date. Implement your expensive
            challenge generation logic here.
        """
        raise NotImplementedError("_generate_challenge must be implemented by subclass")
    
    @abstractmethod
    def check_guess(self, guess: str, secret: str) -> dict[str, Any]:
        """
        Process a guess and return hints/feedback.
        
        Args:
            guess: The player's guess
            secret: The secret word/challenge
            
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
