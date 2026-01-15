from pathlib import Path
from riddle.server_game import GameServer
import sys


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