# Wordle-Like Game Server Architecture

## Overview

Stateless game server using **FastAPI** + **JWT tokens** for session management. No database required.

**Key optimization**: Server caches game instances (one per date per game) to avoid expensive regeneration on every guess.

**Multi-game support**: Run multiple games simultaneously with URL-based routing (e.g., `/wordle-en-5` and `/wordle-fr-5`).

## Architecture Principle

**Stateless Design**: All game state stored in JWT tokens on the client side.

```
Client → Server (with JWT) → Process → Server → Client (with new JWT)
```

**Instance-per-Date-per-Game**: Server maintains a cache of game instances, one for each (slug, date) pair.

```
Server creates/retrieves: 
  GameInstance("wordle-en-5", "2026-01-12") → English Wordle for Jan 12
  GameInstance("wordle-fr-5", "2026-01-12") → French Wordle for Jan 12
```

**URL-based Routing**: Each game has its own URL slug and API endpoints:
- `GET /{slug}` → Game page
- `POST /{slug}/api/guess` → Submit guess
- `POST /{slug}/api/reset` → Reset game
- `GET /{slug}/api/info` → Game info

## File Structure

```
src/
  riddle/
    server_game.py           # Game-agnostic FastAPI server (GameServer class)
    riddle_game.py           # RiddleGame interface for game implementations
    game_state.py            # GameState abstract base class for serializable state
  wordle/
    wordle_game.py           # Wordle game implementation (WordleGame)
    wordle_state.py          # Wordle-specific game state (WordleState)
    main_wordle_server.py    # Server entry point
    main_wordle_cli.py       # Terminal interface (uses WordleState objects)
  static/
    index.html               # Frontend HTML
    game.js                  # Frontend JavaScript
    style.css                # Frontend CSS
data/
  english_words.txt          # Word list for Wordle
```

## How It Works

### 1. Session Flow

1. **First request**: No token → Server creates new game state → Returns JWT
2. **Page load**: Client sends empty guess `""` with token → Server validates hash → Returns current state (or new state if mismatch)
3. **Subsequent requests**: Client sends JWT → Server decodes & validates → Updates state → Returns new JWT
4. **Token storage**: Client saves JWT in `localStorage`
5. **Token expiration**: Automatic at midnight (resets daily challenge)
6. **Hash validation**: Server compares `secret_hash` in token with current secret's hash → Resets if mismatch

### 2. Daily Challenge System with Server-Side Instance Caching

**Server caches game instances, not challenges:**

```python
class GameServer:
    def __init__(self, game_factory: Callable[[str], RiddleGame], ...):
        # Cache of game instances by date
        self._game_cache: dict[str, RiddleGame] = {}
        self.game_factory = game_factory
    
    def get_game_for_date(self, date_str: str) -> RiddleGame:
        """Get or create a game instance for a specific date."""
        if date_str not in self._game_cache:
            # Create NEW instance for this date
            self._game_cache[date_str] = self.game_factory(date_str)
            
            # Keep only last 7 days
            if len(self._game_cache) > 7:
                oldest_date = min(self._game_cache.keys())
                del self._game_cache[oldest_date]
        
        return self._game_cache[date_str]

# Usage in endpoints:
game = server.get_game_for_date("2026-01-12")  # Creates or retrieves instance
result = game.check_guess(player_guess)        # Uses game's stored secret
```

**Game instance structure:**

```python
class RiddleGame:
    def __init__(self, date_str: str):
        self._date = date_str
        self._secret = self._generate_challenge(date_str)  # Generated once
    
    def check_guess(self, guess: str) -> dict:
        # Uses self._secret (no need to pass it around)
        ...
```

**Why server-side instance caching?**
- **Single Responsibility**: Server manages caching, game manages game logic
- **One instance = One date's game**: Each `RiddleGame` instance stores ONE secret
- Challenge generation can be CPU-intensive for complex games
- **Generated once** when instance created, then reused for all guesses
- Cleaner separation: caching concern in server, not in game

**Cache behavior:**
- First request for a date: creates `RiddleGame(date)` instance, stores in cache
- Subsequent requests: retrieves existing instance from cache
- Automatic cleanup: keeps max 7 date instances
- Each instance knows its own secret via `self._secret`

### 3. JWT Token Structure

```json
{
  "date": "2026-01-08",
  "game_state": {
    "guesses": [
      {
        "word": "CRANE",
        "hints": [{"letter": "C", "status": "absent"}, ...],
        "is_correct": false
      }
    ],
    "attempts": 1,
    "max_attempts": 6,
    "won": false,
    "lost": false,
    "game_over": false,
    "secret_hash": "a3c5e7..."
  },
  "exp": 1736294400
}
```

**Security Feature: `secret_hash`**
- SHA256 hash of the secret word
- Validates that client state matches server's current word
- Detects server restarts or secret key changes
- Automatic reset if hash mismatch detected

- **Signed with HMAC**: Prevents client tampering
- **Expires at midnight**: Forces daily reset
- **Self-contained**: No database lookups needed
- **Game state serialization**: `GameState.to_dict()` for encoding, `GameState.from_dict()` for decoding

## Static Files

The server automatically mounts the `src/static/` directory:

```python
self.app.mount("/static", StaticFiles(directory=str(STATIC_FOLDER_PATH)), name="static")
```

This allows the frontend to load:
- `/static/style.css` → CSS styling
- `/static/game.js` → JavaScript game logic

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Serve frontend HTML |
| `/static/*` | GET | Serve static files (CSS, JS) |
| `/api/info` | GET | Get game metadata (date, word length, max attempts) |
| `/api/guess` | POST | Submit guess, returns hints + new token<br>**Empty guess `""` validates token without consuming attempt** |
| `/api/reset` | POST | Reset game, returns fresh token |

## Game Logic (Customizable)

### GameState Interface

All game states inherit from `GameState` in [src/game_state.py](../src/riddle/game_state.py):

```python
class GameState(ABC):
    """
    Abstract base class for game state.
    
    All game states must be serializable to/from dict for JWT storage.
    """
    
    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """
        Convert state to dictionary for JWT encoding.
        
        Returns:
            Dictionary representation of the state
        """
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> 'GameState':
        """
        Reconstruct state from dictionary (from JWT).
        
        Args:
            data: Dictionary representation of the state
            
        Returns:
            GameState instance
        """
        pass
    
    @abstractmethod
    def is_game_over(self) -> bool:
        """
        Check if the game is over.
        
        Returns:
            True if game is over (won or lost)
        """
        pass
```

**Benefits:**
- **Type safety**: Use dataclasses with type hints
- **Clean API**: Object properties instead of dict keys
- **Serialization**: Built-in JWT encoding/decoding
- **Reusable**: Same state class for web, CLI, any interface

### RiddleGame Interface

Games implement the `RiddleGame` interface in [src/riddle/riddle_game.py](../src/riddle/riddle_game.py):

```python
class RiddleGame(ABC):
    """
    Interface for Wordle-like games.
    
    Each instance represents ONE game for ONE specific date.
    The server will cache multiple instances (one per date).
    
    Each game instance stores its own secret and handles guess checking.
    No need for date-based caching - that's the server's responsibility.
    """
    
    def __init__(self, date_str: str):
        """
        Initialize the game instance for a specific date.
        
        Args:
            date_str: The date for this game instance in format "YYYY-MM-DD"
        """
        self._date = date_str
        self._secret = self._generate_challenge(date_str)
    
    @abstractmethod
    def _generate_challenge(self, date_str: str) -> str:
        """
        Generate the challenge/secret for a given date.
        
        Args:
            date_str: Date in format "YYYY-MM-DD"
            
        Returns:
            The generated secret word/challenge
            
        Note:
            Must be deterministic - same date must always return same secret.
            This is called once during __init__ to create the secret.
        """
        raise NotImplementedError("_generate_challenge must be implemented by subclass")
    
    @property
    def secret(self) -> str:
        """Get the secret for this game instance."""
        return self._secret
    
    @property
    def date(self) -> str:
        """Get the date for this game instance."""
        return self._date
    
    @abstractmethod
    def check_guess(self, guess: str) -> dict[str, Any]:
        """
        Process a guess and return hints/feedback.
        
        Uses the secret stored in self._secret (set during __init__).
        
        Args:
            guess: The player's guess
            
        Returns:
            Dictionary containing:
                - "guess": The processed guess (normalized)
                - "hints": List of hint objects (format depends on game)
                - "is_correct": Boolean indicating if guess matches secret
                
        Example for Wordle:
            {
                "guess": "CRANE",
                "hints": [
                    {"letter": "C", "status": "absent"},
                    {"letter": "R", "status": "present"},
                    ...
                ],
                "is_correct": False
            }
        """
        raise NotImplementedError("check_guess must be implemented by subclass")

```

**Key concepts:**
- **One instance = One date**: `RiddleGame("2026-01-12")` is the game for Jan 12
- **Secret stored in instance**: `self._secret` set during `__init__`
- **Typed game state**: Dataclass subclasses of `GameState` for type safety
- **Game manages state**: `check_guess()` accepts and returns `GameState` objects
- **Serialization built-in**: `to_dict()`/`from_dict()` for JWT encoding/decoding
- **Stateless from server perspective**: Server just stores/restores state in JWT
- **Game owns logic**: Win/loss/attempts managed by game, not UI or server
- **No caching in game**: Server handles caching instances

### Current Implementation

The wordle game is inherits from `RiddleGame`. It is a simple example of how to implement a game using the base class. See [wordle_game.py](../src/wordle/wordle_game.py).  

It uses `WordleState` dataclass in [wordle_state.py](../src/wordle/wordle_state.py) to represent the game state.  

It can be run in CLI mode via [main_wordle_cli.py](../src/wordle/main_wordle_cli.py) or as a web server via [main_wordle_server.py](../src/wordle/main_wordle_server.py).


**Key design decisions:**
- **No static variables**: Each instance loads word list independently
- **Allows hot reloading**: Update word file, next instance uses new words
- **Secret key from CLI**: Never in source code (open source safe)
- **Factory closure**: Captures configuration (words_file, secret_key)
- **Slug-based routing**: Each game gets its own URL path and API endpoints

**To create your own game:**
1. Create new file (e.g., `my_game.py`)
2. **Create state dataclass**: Inherit from `GameState`, implement `to_dict()`, `from_dict()`, `is_game_over()`
3. **Create game class**: Inherit from `RiddleGame`
4. Implement `__init__(date_str, ...)` - accept any config needed
5. Implement `_generate_challenge(date_str)` - deterministic secret generation
6. Implement `create_game_state()` - return your state dataclass instance
7. Implement `check_guess(guess, game_state)` - validate, update state, determine win/loss
8. Load resources per-instance (no static variables for hot reload)
9. Create factory function that captures configuration
10. Pass `(slug, factory)` tuples to `GameServer([("my-game", factory)])`

**Multi-game Example:**
```python
# Create multiple game factories
def english_wordle_factory(date_str: str) -> WordleGame:
    return WordleGame(date_str, english_words_file, secret_key)

def french_wordle_factory(date_str: str) -> WordleGame:
    return WordleGame(date_str, french_words_file, secret_key)

# Register both with unique slugs
server = GameServer([
    ("wordle-en-5", english_wordle_factory),
    ("wordle-fr-5", french_wordle_factory)
])
```

This creates:
- `https://yoursite.com/wordle-en-5` → English Wordle
- `https://yoursite.com/wordle-fr-5` → French Wordle

**Pattern:**
- **Dataclass for state**: Type-safe properties, built-in serialization
- **Game manages state**: `check_guess()` accepts and returns typed `GameState` objects
- **Game owns logic**: Win/loss/attempts determined by game, not UI
- **Stateless server**: Server just stores game state in JWT via `to_dict()`/`from_dict()`
- **Instance variables**: Everything (word lists, config, secret)
- **Factory closure**: Captures runtime configuration
- **No class variables**: Enables configuration updates without restart

**Separation of Concerns:**
- **GameState dataclass**: Data structure with serialization
- **RiddleGame**: Game rules, state management, win/loss logic
- **GameServer**: HTTP handling, JWT encoding/decoding, instance caching
- **UI (CLI/Web)**: Display, user input, rendering game state objects

## Frontend Features

- **Auto-save**: Progress stored in `localStorage`
- **Session restoration**: Reloads game state on page refresh
- **Color-coded feedback**: Green (correct), Yellow (present), Gray (absent)
- **Real-time stats**: Attempts counter, remaining tries

## Key Benefits

✅ **Scalable**: Any server can handle any request (no sticky sessions)  
✅ **Simple**: No database, no Redis, no session storage  
✅ **Secure**: JWT signature prevents state forgery  
✅ **Daily reset**: Token expiration handles it automatically  
✅ **Fair**: Everyone gets same challenge on same day  
✅ **Efficient**: Game instances cached in server, generated only once per day  
✅ **Fast**: Subsequent guesses reuse existing game instance  
✅ **Clean architecture**: Server handles caching, games handle game logic  
✅ **Single Responsibility**: Each class has one clear purpose  
✅ **Game-owned state**: All game logic and rules in RiddleGame, not scattered across UI/server  
✅ **Type safety**: Dataclass states with IDE autocomplete and type checking  
✅ **Reusable games**: Same game class works for web, CLI, or any UI  
✅ **Testable**: Game logic isolated and easy to unit test with typed states  
✅ **Hash validation**: Detects server restarts/secret changes, auto-resets stale game states  
✅ **Empty guess validation**: Token validation without consuming attempts

## Running the Server

```bash
# Run the Wordle demo with secret key
uv run src/wordle/main_wordle_server.py "your-super-secret-key-here"

# Production: Use environment variable
export SECRET_KEY="your-secret-key"
uv run src/wordle/main_wordle_server.py

# Or specify port and host
export PORT=8080
export HOST=0.0.0.0
uv run src/wordle/main_wordle_server.py

# Or with your own game
uv run src/my_game/main_server.py <args>
```

Server starts at: http://127.0.0.1:8000

**Default setup** creates a single game at `/wordle-en-5`.

**Root endpoint** (`/`) lists all available games.

**Each game** gets its own URL:
- `http://127.0.0.1:8000/wordle-en-5` → Game page
- `http://127.0.0.1:8000/wordle-en-5/api/guess` → API endpoint
- `http://127.0.0.1:8000/wordle-en-5/api/info` → Game info
- `http://127.0.0.1:8000/wordle-en-5/api/reset` → Reset endpoint

**⚠️ IMPORTANT: Secret Key**
- Required as command-line argument
- Never commit to git or include in source code
- Used to generate daily word selection
- Same key = same words for all players
- Different key = different word sequence
- Generate with: `openssl rand -base64 32`

## Security Considerations

### JWT Security
- **Change `SECRET_KEY`** in GameServer production deployment
- Use environment variables for secrets
- Consider HTTPS in production
- Rate limiting recommended for `/api/guess` endpoint

### Game Secret Key (Word Selection)
- **CRITICAL**: Keep the game secret key private
- Pass via command line argument or environment variable
- Never commit to source control (even for open source projects)
- Without the secret key, players cannot predict future words
- Used in: `hash(date + secret_key)` for deterministic word selection
- Generate strong key: `openssl rand -base64 32`
- Rotate periodically to change word sequence

**Example secure deployment:**
```bash
# Store in environment
export WORDLE_SECRET_KEY="$(openssl rand -base64 32)"

# Run server
uv run src/main_wordle_game.py "${WORDLE_SECRET_KEY}"
```

### Why This Matters (Open Source)
Even though your code is open source:
- Without the secret key, players can't predict tomorrow's word
- They can see the algorithm, but not reproduce your specific sequence
- This allows transparent code while maintaining fair gameplay

## Future Enhancements

- [ ] Add difficulty levels
- [ ] Statistics tracking (win rate, average attempts)
- [ ] Leaderboard (requires database)
- [ ] Share results (emoji grid like Wordle)
- [ ] Multiple game modes
