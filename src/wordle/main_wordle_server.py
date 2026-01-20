from riddle.game_server import GameServer
import sys
import os
from wordle import generate_wordle_factory
from wordle.wordle_game import WordleGame
from riddle.types import Language, GameFactory


def main():
    # Get secret key from environment variable or command line. Or take default "0" for testing.
    if len(sys.argv) >= 2:
        secret_key = sys.argv[1]
    elif os.getenv('SECRET_KEY'):
        secret_key = os.getenv('SECRET_KEY')
    else:
        secret_key = "0"
        print("⚠️  WARNING: Using default SECRET_KEY='0' for testing purposes only. Do not use in production!")

    # Type narrowing: secret_key is definitely str after the check above
    assert secret_key is not None

    # Create game factory that captures configuration
    game_factory_pack: GameFactory[WordleGame] = generate_wordle_factory(Language.EN, 5, secret_key)

    # Create server with slug and factory
    server = GameServer([game_factory_pack])

    # Run the server (will create today's game and show secret for testing)
    # Get port from environment (for deployment) or use default
    host: str
    host_env = os.getenv('HOST')
    if host_env:
        host = host_env
        print(f"🚀 Using 'HOST' from environment: {host}")
    else:
        host = '127.0.0.1'
        print(f"🚀 'HOST' not found in environment. Using default host: {host}")
    
    port: int
    port_env = os.getenv('PORT')
    if port_env:
        port = int(port_env)
        print(f"🚀 Using 'PORT' from environment: {port}")
    else:
        port = 8000
        print(f"🚀 'PORT' not found in environment. Using default port: {port}")

    print(flush=True)
    server.run(host=host, port=port)

if __name__ == "__main__":
    main()