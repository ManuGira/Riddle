from riddle_game import RiddleGame
import hashlib
from pathlib import Path
from server_game import GameServer
from typing import Any
import sys


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
    
    def create_game_state(self) -> dict:
        """
        Create initial game state.
        
        Returns:
            New game state dictionary
        """
        return {
            'guesses': [],
            'attempts': 0,
            'max_attempts': self.MAX_ATTEMPTS,
            'won': False,
            'lost': False,
            'game_over': False
        }
    
    def check_guess(self, guess: str, game_state: dict | None = None) -> dict:
        """
        Check a guess against the secret word and update game state.
        
        Args:
            guess: The guessed word (case-insensitive)
            game_state: Current game state (creates new if None)
            
        Returns:
            Updated game state with new guess result:
            {
                'guesses': [{'word': str, 'hints': [...], 'is_correct': bool}, ...],
                'attempts': int,
                'max_attempts': int,
                'won': bool,
                'lost': bool,
                'game_over': bool
            }
            
        Raises:
            ValueError: If guess is invalid or game is already over
        """
        # Initialize state if needed
        if game_state is None:
            game_state = self.create_game_state()
        else:
            # Create a copy to avoid mutation
            game_state = game_state.copy()
            game_state['guesses'] = game_state['guesses'].copy()
        
        # Check if game is over
        if game_state['game_over']:
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
        guess_result = {
            'word': guess,
            'hints': hints,
            'is_correct': is_correct
        }
        
        # Update game state
        game_state['guesses'].append(guess_result)
        game_state['attempts'] += 1
        
        # Check win/loss conditions
        if is_correct:
            game_state['won'] = True
            game_state['game_over'] = True
        elif game_state['attempts'] >= game_state['max_attempts']:
            game_state['lost'] = True
            game_state['game_over'] = True
        
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