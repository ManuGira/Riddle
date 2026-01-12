# Wordle-Like Game Server Architecture

## Overview

Stateless game server using **FastAPI** + **JWT tokens** for session management. No database required.

**Key optimization**: Server caches game instances (one per date) to avoid expensive regeneration on every guess.

## Architecture Principle

**Stateless Design**: All game state stored in JWT tokens on the client side.

```
Client → Server (with JWT) → Process → Server → Client (with new JWT)
```

**Instance-per-Date**: Server maintains a cache of game instances, one for each date.

```
Server creates/retrieves: GameInstance("2026-01-12") → each instance stores its secret
```

## File Structure

```
src/
  server_game.py           # Game-agnostic FastAPI server (GameServer class)
  riddle_game.py           # RiddleGame interface for game implementations
  game_state.py            # GameState abstract base class for serializable state
  main_wordle_game.py      # Example Wordle implementation (WordleGame + WordleState)
  play_wordle_cli.py       # Terminal interface (uses WordleState objects)
static/
  index.html              # Frontend (HTML + JavaScript)
```

## How It Works

### 1. Session Flow

1. **First request**: No token → Server creates new game state → Returns JWT
2. **Subsequent requests**: Client sends JWT → Server decodes & validates → Updates state → Returns new JWT
3. **Token storage**: Client saves JWT in `localStorage`
4. **Token expiration**: Automatic at midnight (resets daily challenge)

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
    "game_over": false
  },
  "exp": 1736294400
}
```

- **Signed with HMAC**: Prevents client tampering
- **Expires at midnight**: Forces daily reset
- **Self-contained**: No database lookups needed
- **Game state serialization**: `GameState.to_dict()` for encoding, `GameState.from_dict()` for decoding

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Serve frontend HTML |
| `/api/info` | GET | Get game metadata (date, word length, max attempts) |
| `/api/guess` | POST | Submit guess, returns hints + new token |
| `/api/reset` | POST | Reset game, returns fresh token |

## Game Logic (Customizable)

### GameState Interface

All game states inherit from `GameState` in [src/game_state.py](../src/game_state.py):

```python
class GameState(ABC):
    """
    Abstract base class for game state.
    All game states must be serializable to/from dict for JWT storage.
    """
    
    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert state to dictionary for JWT encoding."""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> 'GameState':
        """Reconstruct state from dictionary (from JWT)."""
        pass
    
    @abstractmethod
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        pass
```

**Benefits:**
- **Type safety**: Use dataclasses with type hints
- **Clean API**: Object properties instead of dict keys
- **Serialization**: Built-in JWT encoding/decoding
- **Reusable**: Same state class for web, CLI, any interface

### RiddleGame Interface

Games implement the `RiddleGame` interface in [src/riddle_game.py](../src/riddle_game.py):

```python
class RiddleGame(ABC):
    """
    Each instance represents ONE game for ONE specific date.
    Server caches multiple instances (one per date).
    
    GAME STATE PHILOSOPHY:
    - RiddleGame owns all game logic and state management
    - check_guess() accepts and returns complete game state
    - Win/loss conditions determined by the game, not UI/server
    - Game state is opaque to server (just stores it in JWT)
    """
    
    def __init__(self, date_str: str):
        """
        Create game instance for a specific date.
        Generates and stores the secret during initialization.
        """
        self._date = date_str
        self._secret = self._generate_challenge(date_str)
    
    @abstractmethod
    def _generate_challenge(self, date_str: str) -> str:
        """
        Generate the secret for this date.
        Called ONCE during __init__ - implement your expensive logic here.
        Must be deterministic (same date = same secret).
        """
        pass
    
    @property
    def secret(self) -> str:
        """Get this game's secret."""
        return self._secret
    
    @abstractmethod
    def create_game_state(self) -> GameState:
        """
        Create initial game state.
        Return your game's specific GameState subclass.
        """
        pass
    
    @abstractmethod
    def check_guess(self, guess: str, game_state: GameState | None = None) -> GameState:
        """
        Process a guess and update game state.
        
        Args:
            guess: Player's guess
            game_state: Current game state (None for new game)
        
        Returns:
            Updated GameState instance (your game's specific subclass)
        
        The game is responsible for:
        - Validating guesses
        - Determining win/loss conditions
        - Tracking attempts and limits
        - Managing all game rules
        """
        pass
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

Example in [main_wordle_game.py](../src/main_wordle_game.py):

```python
from dataclasses import dataclass, field
from game_state import GameState

@dataclass
class GuessResult:
    """Result of a single guess."""
    word: str
    hints: list[dict[str, str]]  # [{'letter': 'A', 'status': 'correct'}, ...]
    is_correct: bool

@dataclass
class WordleState(GameState):
    """Game state for Wordle."""
    guesses: list[GuessResult] = field(default_factory=list)
    attempts: int = 0
    max_attempts: int = 6
    won: bool = False
    lost: bool = False
    game_over: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JWT encoding."""
        return {
            'guesses': [
                {'word': g.word, 'hints': g.hints, 'is_correct': g.is_correct}
                for g in self.guesses
            ],
            'attempts': self.attempts,
            'max_attempts': self.max_attempts,
            'won': self.won,
            'lost': self.lost,
            'game_over': self.game_over
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'WordleState':
        """Reconstruct from dictionary (from JWT)."""
        guesses = [
            GuessResult(word=g['word'], hints=g['hints'], is_correct=g['is_correct'])
            for g in data.get('guesses', [])
        ]
        return cls(
            guesses=guesses,
            attempts=data.get('attempts', 0),
            max_attempts=data.get('max_attempts', 6),
            won=data.get('won', False),
            lost=data.get('lost', False),
            game_over=data.get('game_over', False)
        )
    
    def is_game_over(self) -> bool:
        return self.game_over

class WordleGame(RiddleGame):
    """Each instance is for one specific date."""
    
    MAX_ATTEMPTS = 6  # Game rule: standard Wordle limit
    
    def __init__(self, date_str: str, words_file: Path, secret_key: str):
        """Create game for specific date."""
        self.words_file = words_file
        self.secret_key = secret_key
        self.word_list = self._load_words(words_file)
        super().__init__(date_str)
    
    def _generate_challenge(self, date_str: str) -> str:
        """Generate secret using deterministic hash with secret_key."""
        hash_val = int(hashlib.sha256((date_str + self.secret_key).encode()).hexdigest(), 16)
        return self.word_list[hash_val % len(self.word_list)]
    
    def create_game_state(self) -> WordleState:
        """Create initial Wordle game state."""
        return WordleState(max_attempts=self.MAX_ATTEMPTS)
    
    def check_guess(self, guess: str, game_state: WordleState | None = None) -> WordleState:
        """
        Check guess and update game state.
        
        Returns WordleState object with type-safe properties:
        - state.attempts (int)
        - state.guesses (list[GuessResult])
        - state.won, state.lost (bool)
        """
        # Initialize or copy state
        if game_state is None:
            game_state = self.create_game_state()
        else:
            # Copy to avoid mutation
            game_state = WordleState(
                guesses=game_state.guesses.copy(),
                attempts=game_state.attempts,
                max_attempts=game_state.max_attempts,
                won=game_state.won,
                lost=game_state.lost,
                game_over=game_state.game_over
            )
        
        # Validate and process guess
        if game_state.is_game_over():
            raise ValueError("Game is already over")
        
        guess = guess.upper().strip()
        if len(guess) != 5:
            raise ValueError("Guess must be 5 letters")
        if guess not in self.word_list:
            raise ValueError(f"'{guess}' not in word list")
        
        # Generate hints
        hints = self._generate_hints(guess)
        
        # Create typed guess result
        is_correct = guess == self._secret
        guess_result = GuessResult(
            word=guess,
            hints=hints,
            is_correct=is_correct
        )
        
        # Update state using type-safe properties
        game_state.guesses.append(guess_result)
        game_state.attempts += 1
        
        # Determine win/loss
        if is_correct:
            game_state.won = True
            game_state.game_over = True
        elif game_state.attempts >= game_state.max_attempts:
            game_state.lost = True
            game_state.game_over = True
        
        return game_state

# In main:
if __name__ == "__main__":
    secret_key = sys.argv[1]
    words_file = Path(__file__).parent.parent / "data" / "english_words.txt"
    
    def game_factory(date_str: str) -> WordleGame:
        return WordleGame(date_str, words_file, secret_key)
    
    server = GameServer(game_factory)
    server.run()
```

**Dataclass benefits:**
- **Type safety**: `state.attempts` instead of `state['attempts']`
- **IDE support**: Autocomplete and type checking
- **Clean API**: Use objects in code, serialize to dict for JWT
- **Reusable**: Same `WordleState` class for web, CLI, any interface
- **Testable**: Easy to construct test states with named parameters

**Key design decisions:**
- **No static variables**: Each instance loads word list independently
- **Allows hot reloading**: Update word file, next instance uses new words
- **Secret key from CLI**: Never in source code (open source safe)
- **Factory closure**: Captures configuration (words_file, secret_key)

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
10. Pass factory to `GameServer(factory)`

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

## Running the Server

```bash
# Run the Wordle demo with secret key
uv run src/main_wordle_game.py "your-super-secret-key-here"

# Production: Use environment variable
uv run src/main_wordle_game.py "${WORDLE_SECRET_KEY}"

# Or with your own game
uv run src/my_game.py <args>
```

Server starts at: http://127.0.0.1:8000

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
