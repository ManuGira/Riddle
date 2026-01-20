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
from riddle.types import Language
import sys
import os
from wordle import generate_wordle_factory


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
    
    assert secret_key is not None
    
    # Create game factories for wordle games

    game_factories = []
    for lang in [Language.EN, Language.FR]:
        for length in range(3, 10):
            wordle_factory = generate_wordle_factory(lang, length, secret_key)
            game_factories.append(wordle_factory)

    
    # Create server with multiple games
    server = GameServer(game_factories)
    
    print("🎮 Multi-Language Wordle Server Starting...")
    print(f"🔐 Secret key: {'*' * len(secret_key)} (hidden)")
    print("\n📚 Game Configuration:")
    print("\n🌍 Available Games:")
    print("  - http://127.0.0.1:8000/ (lists all games)")
    for slug, _ in server.url_to_factory_map.items():
        print(f"  - http://127.0.0.1:8000/{slug}")
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
