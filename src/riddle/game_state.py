"""
Game state interface and utilities for state management.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Any


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
