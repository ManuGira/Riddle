"""
Example: Multi-language Wordle server
Demonstrates running English and French Wordle simultaneously.

Usage:
    uv run src/wordle/main_multi_wordle_server.py <SECRET_KEY>

Endpoints:
    http://127.0.0.1:8000/                → List of available games
    http://127.0.0.1:8000/wordle-en-5     → English Wordle (5 letters)
    http://127.0.0.1:8000/wordle-fr-5     → French Wordle (5 letters)
"""

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
        print("Usage: uv run src/wordle/main_multi_wordle_server.py <SECRET_KEY>")
        print("Or set SECRET_KEY environment variable")
        print("Example: uv run src/wordle/main_multi_wordle_server.py my-secret-2026")
        print("\nWARNING: Keep SECRET_KEY private! Don't commit it to git.")
        sys.exit(1)
    
    # Type narrowing: secret_key is definitely str after the check above
    assert secret_key is not None
    
    # Configuration for each game
    english_words_file = DATA_FOLDER_PATH / "english_words.txt"
    french_words_file = DATA_FOLDER_PATH / "words_lists" / "wordle_list_FR_L5_base.txt"
    
    # Create game factories
    def english_wordle_factory(date_str: str) -> WordleGame:
        return WordleGame(date_str, english_words_file, secret_key)
    
    def french_wordle_factory(date_str: str) -> WordleGame:
        return WordleGame(date_str, french_words_file, secret_key)
    
    # Create server with multiple games
    server = GameServer([
        ("wordle-en-5", english_wordle_factory),
        ("wordle-fr-5", french_wordle_factory)
    ])
    
    print("🎮 Multi-Language Wordle Server Starting...")
    print(f"🔐 Secret key: {'*' * len(secret_key)} (hidden)")
    print("\n📚 Game Configuration:")
    print(f"  English words: {english_words_file}")
    print(f"  French words:  {french_words_file}")
    print("\n🌍 Available Games:")
    print("  English: http://127.0.0.1:8000/wordle-en-5")
    print("  French:  http://127.0.0.1:8000/wordle-fr-5")
    print("  Root:    http://127.0.0.1:8000/ (lists all games)")
    print("\n⚠️  Keep the secret key private - it's used to generate daily words!")
    
    # Get port and host from environment or use defaults
    host: str
    host_env = os.getenv('HOST')
    if host_env:
        host = host_env
        print(f"\n🚀 Using 'HOST' from environment: {host}")
    else:
        host = '127.0.0.1'
        print(f"\n🚀 Using default host: {host}")
    
    port: int
    port_env = os.getenv('PORT')
    if port_env:
        port = int(port_env)
        print(f"🚀 Using 'PORT' from environment: {port}")
    else:
        port = 8000
        print(f"🚀 Using default port: {port}")

    print(flush=True)
    server.run(host=host, port=port)


if __name__ == "__main__":
    main()
