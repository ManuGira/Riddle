from riddle.game_state import GameState
from typing import Any
from dataclasses import dataclass, field


@dataclass
class GuessResult:
    """Result of a single guess."""
    word: str
    hints: list[dict[str, str]]  # [{'letter': 'A', 'status': 'correct'}, ...]
    is_correct: bool


@dataclass
class WordleState(GameState):
    """Game state for Wordle."""
    guesses: list[GuessResult] = field(default_factory=list)
    attempts: int = 0
    max_attempts: int = 6
    won: bool = False
    lost: bool = False
    game_over: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JWT encoding."""
        return {
            'guesses': [
                {
                    'word': g.word,
                    'hints': g.hints,
                    'is_correct': g.is_correct
                }
                for g in self.guesses
            ],
            'attempts': self.attempts,
            'max_attempts': self.max_attempts,
            'won': self.won,
            'lost': self.lost,
            'game_over': self.game_over
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'WordleState':
        """Reconstruct from dictionary (from JWT)."""
        guesses = [
            GuessResult(
                word=g['word'],
                hints=g['hints'],
                is_correct=g['is_correct']
            )
            for g in data.get('guesses', [])
        ]
        
        return cls(
            guesses=guesses,
            attempts=data.get('attempts', 0),
            max_attempts=data.get('max_attempts', 6),
            won=data.get('won', False),
            lost=data.get('lost', False),
            game_over=data.get('game_over', False)
        )
    
    def is_game_over(self) -> bool:
        """Check if game is over."""
        return self.game_over
    