"""
Command-line Wordle game.
Play Wordle directly in your terminal.
"""

import dataclasses

from wordle import generate_wordle_factory
from wordle.wordle_game import WordleGame
from wordle.wordle_state import WordleState
from datetime import datetime
import sys
from riddle import GameFactory, Language


@dataclasses.dataclass
class Colors:
    # ANSI color codes for terminal output
    GOOD = '\033[102m'
    WARNING = '\033[103m'
    BAD = '\033[101m'
    GRAY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class WordleCLI:
    """Terminal-based Wordle game interface."""
    
    def __init__(self, game: WordleGame):
        """
        Initialize the CLI game.
        
        Args:
            game: WordleGame instance for today
        """
        self.game: WordleGame = game
        self.game_state: WordleState = game.create_game_state()
    
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
            return f"{Colors.GOOD}{Colors.BOLD}{letter}{Colors.RESET}"
        elif status == 'present':
            return f"{Colors.WARNING}{Colors.BOLD}{letter}{Colors.RESET}"
        else:  # absent
            return f"{Colors.GRAY}{letter}{Colors.RESET}"
    
    def display_guess(self, guess_result):
        """Display a guess with colored hints."""
        colored_letters = []
        for hint in guess_result.hints:
            colored_letters.append(self.colorize_hint(f" {hint['letter']} ", hint['status']))
        
        print("  " + "".join(colored_letters))
    
    def display_board(self):
        """Display the current game board."""
        print("\n" + "="*40)
        print(f"  WORDLE - Attempt {self.game_state.attempts}/{self.game_state.max_attempts}")
        print("="*40)
        
        # Show all previous guesses
        for guess_result in self.game_state.guesses:
            self.display_guess(guess_result)
        
        # Show remaining empty rows
        for _ in range(self.game_state.max_attempts - len(self.game_state.guesses)):
            print("   _  _  _  _  _")
        
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
        print(f"{Colors.BOLD}WELCOME TO WORDLE!{Colors.RESET}")
        print("🎮 "*10)
        
        print(f"\n📅 Today's date: {self.game.date}")
        print(f"🎯 You have {self.game_state.max_attempts} attempts to guess the word")
        
        self.display_legend()
        
        while not self.game_state.is_game_over():
            self.display_board()
            
            # Get guess from player
            guess = self.get_guess()
            
            # Check guess and update game state
            try:
                self.game_state = self.game.check_guess(guess, self.game_state)
                
                # Check if game ended
                if self.game_state.is_game_over():
                    self.display_board()
                    if self.game_state.won:
                        self.display_victory()
                    else:
                        self.display_defeat()
                    return
                
            except ValueError as e:
                print(f"❌ {e}")
                continue
    
    def display_victory(self):
        """Display victory message."""
        print("\n" + "🎉 "*15)
        print(f"{Colors.GOOD}{Colors.BOLD}CONGRATULATIONS! YOU WON!{Colors.RESET}")
        print("🎉 "*15)
        print(f"\n✨ You guessed the word in {self.game_state.attempts}/{self.game_state.max_attempts} attempts!")
        print(f"🎯 The word was: {Colors.BOLD}{self.game.secret}{Colors.RESET}\n")
    
    def display_defeat(self):
        """Display defeat message."""
        print("\n" + "💔 "*15)
        print(f"{Colors.GRAY}GAME OVER{Colors.RESET}")
        print("💔 "*15)
        print(f"\n😔 You've used all {self.game_state.max_attempts} attempts.")
        print(f"🎯 The word was: {Colors.BOLD}{self.game.secret}{Colors.RESET}\n")
        print("Better luck next time! 💪\n")


def main():
    """Run the terminal Wordle game."""
    # Get secret key from command line
    if len(sys.argv) < 2:
        import numpy as np
        secret_key = str(np.random.randint(0, 1_000_000))
    else:
        secret_key = sys.argv[1]
    
    # Configuration
    today = datetime.now().strftime("%Y-%m-%d")

    # Create game factory that captures configuration
    wordle_game_factory: GameFactory[WordleGame] = generate_wordle_factory(Language.EN, 5, secret_key)

    # Create game for today
    print("\n🔄 Loading game...")
    wordle_game: WordleGame = wordle_game_factory.create_game_instance(today)

    print("✅ Game loaded!")
    print(f"📊 Word pool size: {len(wordle_game.word_list)}")
    
    # Create and run CLI
    cli = WordleCLI(wordle_game)
    cli.play()


if __name__ == "__main__":
    main()
