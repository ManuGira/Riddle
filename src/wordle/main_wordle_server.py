from riddle.game_server import GameServer
from wordle.wordle_game import WordleGame
import sys
import os
from riddle import DATA_FOLDER_PATH


def main():
    # Get secret key from environment variable or command line
    
    if len(sys.argv) >= 2:
        secret_key = sys.argv[1]
    else:
        secret_key = os.getenv('SECRET_KEY')

    if not secret_key:
        print("Usage: uv run src/wordle/main_wordle_server.py <SECRET_KEY>")
        print("Or set SECRET_KEY environment variable")
        print("Example: uv run src/wordle/main_wordle_server.py my-super-secret-password-2026")
        print("\nWARNING: Keep SECRET_KEY private! Don't commit it to git.")
        sys.exit(1)
    
    # Type narrowing: secret_key is definitely str after the check above
    assert secret_key is not None
    
    # Configuration (can be changed without restart - no static variables!)
    words_file = DATA_FOLDER_PATH / "english_words.txt"
    
    # Create game factory that captures configuration
    def game_factory(date_str: str) -> WordleGame:
        return WordleGame(date_str, words_file, secret_key)
    
    # Create server with factory
    server = GameServer(game_factory)
    
    print("🎮 Wordle Server Starting...")
    print(f"📁 Word list: {words_file}")
    print(f"🔐 Secret key: {'*' * len(secret_key)} (hidden)")
    print("📊 Word pool size: Will be loaded per game instance")
    print("⚠️  Keep the secret key private - it's used to generate daily words!")
    
    # Run the server (will create today's game and show secret for testing)
    # Get port from environment (for deployment) or use default
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '127.0.0.1')
    
    server.run(host=host, port=port)

if __name__ == "__main__":
    main()