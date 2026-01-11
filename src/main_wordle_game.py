from riddle import RiddleGame
import hashlib
from pathlib import Path
from server_game import GameServer
from typing import Any

class WordleGame(RiddleGame):        
        def __init__(self, words_file: Path, seed: int):
            super().__init__()
            # Load word list
            self.seed = seed
            try:
                with open(words_file, "r", encoding="utf-8") as f:
                    words = [w.strip().upper() for w in f if len(w.strip()) == 5]
                self.word_list = [w for w in words if w.isalpha()]
            except FileNotFoundError:
                self.word_list = ["APPLE", "CRANE", "STOLE", "BEACH", "DREAM", "GLOBE"]
        
        def _generate_challenge(self, date_str: str) -> str:
            hash_val = int(hashlib.sha256((date_str + str(self.seed)).encode()).hexdigest(), 16)
            return self.word_list[hash_val % len(self.word_list)]
        
        def check_guess(self, guess: str, secret: str) -> dict[str, Any]:
            guess = guess.upper().strip()
            secret = secret.upper()
            
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
        

if __name__ == "__main__":
    # Example: Import and instantiate your game implementation
    # from my_game import MyCustomGame
    # game = MyCustomGame()
    
    
    # Create game instance and server
    words_file = Path(__file__).parent.parent / "data" / "english_words.txt"
    game = WordleGame(words_file, seed=42)  # TODO: get seed from args
    server = GameServer(game)
    
    print(f"Today's secret (for testing): {game.get_daily_challenge(server.get_today_date())}")
    print(f"Word pool size: {len(game.word_list)}")
    
    # Run the server
    server.run()