from riddle_game import RiddleGame
from game_state import GameState
import hashlib
from pathlib import Path
from server_game import GameServer
from typing import Any
from dataclasses import dataclass, field, asdict
import sys


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


class WordleGame(RiddleGame):
    """Wordle game implementation - each instance is for one specific date."""
    
    MAX_ATTEMPTS = 6  # Standard Wordle rules
    
    def __init__(self, date_str: str, words_file: Path, secret_key: str):
        """
        Create a game instance for a specific date.
        
        Args:
            date_str: Date for this game
            words_file: Path to word list (can change between instances)
            secret_key: Secret key for word selection (keep this private!)
        """
        self.words_file = words_file
        self.secret_key = secret_key
        
        # Load word list (fresh load each time - allows updates without restart)
        try:
            with open(words_file, "r", encoding="utf-8") as f:
                words = [w.strip().upper() for w in f if len(w.strip()) == 5]
            self.word_list = [w for w in words if w.isalpha()]
        except FileNotFoundError:
            self.word_list = ["APPLE", "CRANE", "STOLE", "BEACH", "DREAM", "GLOBE"]
        
        # Call parent __init__ which calls _generate_challenge
        super().__init__(date_str)
    
    def _generate_challenge(self, date_str: str) -> str:
        """
        Generate the secret word for this date using deterministic hash.
        Uses date + secret_key to prevent players from predicting words.
        """
        hash_val = int(hashlib.sha256((date_str + self.secret_key).encode()).hexdigest(), 16)
        return self.word_list[hash_val % len(self.word_list)]
    
    def create_game_state(self) -> WordleState:
        """
        Create initial game state.
        
        Returns:
            New WordleState instance
        """
        return WordleState(max_attempts=self.MAX_ATTEMPTS)
    
    def check_guess(self, guess: str, game_state: WordleState | None = None) -> WordleState:
        """
        Check a guess against the secret word and update game state.
        
        Args:
            guess: The guessed word (case-insensitive)
            game_state: Current game state (creates new if None)
            
        Returns:
            Updated WordleState instance
            
        Raises:
            ValueError: If guess is invalid or game is already over
        """
        # Initialize state if needed
        if game_state is None:
            game_state = self.create_game_state()
        else:
            # Create a copy to avoid mutation (dataclass is mutable)
            game_state = WordleState(
                guesses=game_state.guesses.copy(),
                attempts=game_state.attempts,
                max_attempts=game_state.max_attempts,
                won=game_state.won,
                lost=game_state.lost,
                game_over=game_state.game_over
            )
        
        # Check if game is over
        if game_state.is_game_over():
            raise ValueError("Game is already over")
        
        guess = guess.upper().strip()
        secret = self._secret.upper()
        
        # Validate guess
        if len(guess) != len(secret):
            raise ValueError(f"Guess must be {len(secret)} letters")
        
        if not guess.isalpha():
            raise ValueError("Guess must contain only letters")
        
        if guess not in self.word_list:
            raise ValueError(f"'{guess}' is not in the word list")
        
        # Generate hints using Wordle logic
        hints = []
        secret_letters = list(secret)
        
        # First pass: mark correct positions
        for i, letter in enumerate(guess):
            if letter == secret[i]:
                hints.append({'letter': letter, 'status': 'correct'})
                secret_letters[i] = None  # Mark as used
            else:
                hints.append({'letter': letter, 'status': 'pending'})
        
        # Second pass: mark present letters
        for i, hint in enumerate(hints):
            if hint['status'] == 'pending':
                letter = guess[i]
                if letter in secret_letters:
                    hints[i]['status'] = 'present'
                    secret_letters[secret_letters.index(letter)] = None
                else:
                    hints[i]['status'] = 'absent'
        
        # Create guess result
        is_correct = guess == secret
        guess_result = GuessResult(
            word=guess,
            hints=hints,
            is_correct=is_correct
        )
        
        # Update game state
        game_state.guesses.append(guess_result)
        game_state.attempts += 1
        
        # Check win/loss conditions
        if is_correct:
            game_state.won = True
            game_state.game_over = True
        elif game_state.attempts >= game_state.max_attempts:
            game_state.lost = True
            game_state.game_over = True
        
        return game_state

def main():
    # Get secret key from command line argument
    if len(sys.argv) < 2:
        print("Usage: uv run src/main_wordle_game.py <SECRET_KEY>")
        print("Example: uv run src/main_wordle_game.py my-super-secret-password-2026")
        print("\nWARNING: Keep SECRET_KEY private! Don't commit it to git.")
        sys.exit(1)
    
    secret_key = sys.argv[1]
    
    # Configuration (can be changed without restart - no static variables!)
    words_file = Path(__file__).parent.parent / "data" / "english_words.txt"
    
    # Create game factory that captures configuration
    def game_factory(date_str: str) -> WordleGame:
        return WordleGame(date_str, words_file, secret_key)
    
    # Create server with factory
    server = GameServer(game_factory)
    
    print(f"🎮 Wordle Server Starting...")
    print(f"📁 Word list: {words_file}")
    print(f"🔐 Secret key: {'*' * len(secret_key)} (hidden)")
    print(f"📊 Word pool size: Will be loaded per game instance")
    print(f"⚠️  Keep the secret key private - it's used to generate daily words!")
    
    # Run the server (will create today's game and show secret for testing)
    server.run()

if __name__ == "__main__":
    main()