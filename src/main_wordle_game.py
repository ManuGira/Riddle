from riddle_game import RiddleGame
import hashlib
from pathlib import Path
from server_game import GameServer
from typing import Any
import sys


class WordleGame(RiddleGame):
    """Wordle game implementation - each instance is for one specific date."""
    
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
    
    def check_guess(self, guess: str) -> dict[str, Any]:
        """Check a guess against this game's secret."""
        guess = guess.upper().strip()
        secret = self._secret.upper()
        
        if len(guess) != len(secret):
            raise ValueError(f"Guess must be {len(secret)} letters")
        
        hints = []
        for i, letter in enumerate(guess):
            if letter == secret[i]:
                hints.append({"letter": letter, "status": "correct"})
            elif letter in secret:
                hints.append({"letter": letter, "status": "present"})
            else:
                hints.append({"letter": letter, "status": "absent"})
        
        return {"guess": guess, "hints": hints, "is_correct": guess == secret}

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