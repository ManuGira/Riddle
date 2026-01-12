"""
Command-line Wordle game.
Play Wordle directly in your terminal.
"""

from main_wordle_game import WordleGame
from pathlib import Path
from datetime import datetime
import sys


class WordleCLI:
    """Terminal-based Wordle game interface."""
    
    # ANSI color codes for terminal output
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    GRAY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def __init__(self, game: WordleGame, max_attempts: int = 6):
        """
        Initialize the CLI game.
        
        Args:
            game: WordleGame instance for today
            max_attempts: Maximum number of guesses allowed
        """
        self.game = game
        self.max_attempts = max_attempts
        self.guesses = []
        self.attempts = 0
        self.won = False
    
    def colorize_hint(self, letter: str, status: str) -> str:
        """
        Apply color to a letter based on its status.
        
        Args:
            letter: The letter to colorize
            status: 'correct', 'present', or 'absent'
        
        Returns:
            Colored letter string
        """
        if status == 'correct':
            return f"{self.GREEN}{self.BOLD}{letter}{self.RESET}"
        elif status == 'present':
            return f"{self.YELLOW}{self.BOLD}{letter}{self.RESET}"
        else:  # absent
            return f"{self.GRAY}{letter}{self.RESET}"
    
    def display_guess(self, result: dict):
        """Display a guess with colored hints."""
        colored_letters = []
        for hint in result['hints']:
            colored_letters.append(self.colorize_hint(hint['letter'], hint['status']))
        
        print("  " + " ".join(colored_letters))
    
    def display_board(self):
        """Display the current game board."""
        print("\n" + "="*40)
        print(f"  WORDLE - Attempt {self.attempts}/{self.max_attempts}")
        print("="*40)
        
        # Show all previous guesses
        for result in self.guesses:
            self.display_guess(result)
        
        # Show remaining empty rows
        for _ in range(self.max_attempts - len(self.guesses)):
            print("  _ _ _ _ _")
        
        print()
    
    def display_legend(self):
        """Display color legend."""
        print("\nLegend:")
        print(f"  {self.colorize_hint('X', 'correct')} = Correct position")
        print(f"  {self.colorize_hint('X', 'present')} = Wrong position")
        print(f"  {self.colorize_hint('X', 'absent')} = Not in word")
        print()
    
    def get_guess(self) -> str:
        """
        Get a valid guess from the user.
        
        Returns:
            Valid 5-letter guess in uppercase
        """
        while True:
            try:
                guess = input("Enter your guess (5 letters): ").strip().upper()
                
                if len(guess) != 5:
                    print("❌ Please enter exactly 5 letters!")
                    continue
                
                if not guess.isalpha():
                    print("❌ Please use only letters!")
                    continue
                
                return guess
            
            except KeyboardInterrupt:
                print("\n\n👋 Game cancelled. Goodbye!")
                sys.exit(0)
    
    def play(self):
        """Main game loop."""
        print("\n" + "🎮 "*10)
        print(f"{self.BOLD}WELCOME TO WORDLE!{self.RESET}")
        print("🎮 "*10)
        
        print(f"\n📅 Today's date: {self.game.date}")
        print(f"🎯 You have {self.max_attempts} attempts to guess the word")
        
        self.display_legend()
        
        while self.attempts < self.max_attempts and not self.won:
            self.display_board()
            
            # Get guess from player
            guess = self.get_guess()
            
            # Check guess
            try:
                result = self.game.check_guess(guess)
                self.guesses.append(result)
                self.attempts += 1
                
                # Check if won
                if result['is_correct']:
                    self.won = True
                    self.display_board()
                    self.display_victory()
                    return
                
            except ValueError as e:
                print(f"❌ {e}")
                continue
        
        # Game over
        if not self.won:
            self.display_board()
            self.display_defeat()
    
    def display_victory(self):
        """Display victory message."""
        print("\n" + "🎉 "*15)
        print(f"{self.GREEN}{self.BOLD}CONGRATULATIONS! YOU WON!{self.RESET}")
        print("🎉 "*15)
        print(f"\n✨ You guessed the word in {self.attempts}/{self.max_attempts} attempts!")
        print(f"🎯 The word was: {self.BOLD}{self.game.secret}{self.RESET}\n")
    
    def display_defeat(self):
        """Display defeat message."""
        print("\n" + "💔 "*15)
        print(f"{self.GRAY}GAME OVER{self.RESET}")
        print("💔 "*15)
        print(f"\n😔 You've used all {self.max_attempts} attempts.")
        print(f"🎯 The word was: {self.BOLD}{self.game.secret}{self.RESET}\n")
        print("Better luck next time! 💪\n")


def main():
    """Run the terminal Wordle game."""
    # Get secret key from command line
    if len(sys.argv) < 2:
        print("Usage: uv run src/play_wordle_cli.py <SECRET_KEY>")
        print("Example: uv run src/play_wordle_cli.py my-secret-key")
        print("\n⚠️  Use the same secret key as your server for consistent words!")
        sys.exit(1)
    
    secret_key = sys.argv[1]
    
    # Configuration
    words_file = Path(__file__).parent.parent / "data" / "english_words.txt"
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Create game for today
    print("\n🔄 Loading game...")
    game = WordleGame(today, words_file, secret_key)
    
    print(f"✅ Game loaded!")
    print(f"📊 Word pool size: {len(game.word_list)}")
    
    # Create and run CLI
    cli = WordleCLI(game)
    cli.play()


if __name__ == "__main__":
    main()
