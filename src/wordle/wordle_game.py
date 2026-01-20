from riddle.types import RiddleGame
from riddle.types import GameState
from .wordle_state import WordleState, GuessResult
import hashlib
from pathlib import Path


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
        with open(words_file, "r", encoding="utf-8") as f:
            self.word_list = [w.strip().upper() for w in f]

        # remove last word if empty  (trailing newline)
        self.word_list = [w for w in self.word_list if len(w) > 0]

        assert len(self.word_list) == len(set(self.word_list)), "Word list contains duplicate words"
        assert all(w for w in self.word_list if w.isalpha()) , "All words must be alphabetic"

        word_length = len(self.word_list[0])
        assert all(len(w) == word_length for w in self.word_list), "All words must have the same length"

        print(f"Loaded {len(self.word_list)} words from {words_file} ------------------------------------")
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
        secret_hash = hashlib.sha256(self._secret.encode()).hexdigest()
        return WordleState(max_attempts=self.MAX_ATTEMPTS, secret_hash=secret_hash)
    
    def check_guess(self, guess: str, game_state: GameState | None = None) -> WordleState:
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
            # Type narrowing: game_state must be WordleState for this game
            assert isinstance(game_state, WordleState), "Expected WordleState"
            # Validate that game state matches current secret
            current_hash = hashlib.sha256(self._secret.encode()).hexdigest()
            if game_state.secret_hash and game_state.secret_hash != current_hash:
                raise ValueError("Game state is for a different word. Please reset.")
            
            # Create a copy to avoid mutation (dataclass is mutable)
            game_state = WordleState(
                guesses=game_state.guesses.copy(),
                attempts=game_state.attempts,
                max_attempts=game_state.max_attempts,
                won=game_state.won,
                lost=game_state.lost,
                game_over=game_state.game_over,
                secret_hash=game_state.secret_hash or current_hash
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