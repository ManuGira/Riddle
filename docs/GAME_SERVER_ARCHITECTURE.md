# Wordle-Like Game Server Architecture

## Overview

Stateless game server using **FastAPI** + **JWT tokens** for session management. No database required.

**Key optimization**: Daily challenges are cached to avoid expensive regeneration on every guess.

## Architecture Principle

**Stateless Design**: All game state stored in JWT tokens on the client side.

```
Client → Server (with JWT) → Process → Server → Client (with new JWT)
```

## File Structure

```
src/
  server_game.py           # Game-agnostic FastAPI server (GameServer class)
  gamle.py                 # IGamle interface for game implementations
  simple_wordle_game.py    # Example Wordle implementation
static/
  index.html              # Frontend (HTML + JavaScript)
```

## How It Works

### 1. Session Flow

1. **First request**: No token → Server creates new game state → Returns JWT
2. **Subsequent requests**: Client sends JWT → Server decodes & validates → Updates state → Returns new JWT
3. **Token storage**: Client saves JWT in `localStorage`
4. **Token expiration**: Automatic at midnight (resets daily challenge)

### 2. Daily Challenge System with Caching

**Challenge caching is handled internally by the game instance:**

```python
class SimpleWordleGame(IGamle):
    def __init__(self):
        super().__init__()  # Initializes internal _challenge_cache
        self.word_list = WORD_LIST
    
    def _generate_challenge(self, date_str: str) -> str:
        """Called only once per date, then cached."""
        hash_val = int(hashlib.sha256(date_str.encode()).hexdigest(), 16)
        return self.word_list[hash_val % len(self.word_list)]

# Create single game instance at server startup
game = SimpleWordleGame()

# Use throughout the application
secret = game.get_daily_challenge("2026-01-08")  # Generated and cached
secret = game.get_daily_challenge("2026-01-08")  # Returns cached value
```

**Why instance-based caching?**
- Challenge generation can be CPU-intensive for complex games
- Game instance stores cache internally (`self._challenge_cache`)
- Single instance created at server startup, persists through all requests
- **Generated once per day** on first request, cached for all subsequent requests
- Cleaner OOP design - cache is encapsulated in the game class

**Cache behavior:**
- First request of the day: calls `_generate_challenge()` and caches
- All other requests: instant lookup from `self._challenge_cache`
- Automatic cleanup: keeps max 7 days
- Thread-safe for single-process servers

### 3. JWT Token Structure

```json
{
  "date": "2026-01-08",
  "guesses": [{"guess": "CRANE", "hints": [...]}],
  "attempts": 1,
  "completed": false,
  "won": false,
  "exp": 1736294400
}
```

- **Signed with HMAC**: Prevents client tampering
- **Expires at midnight**: Forces daily reset
- **Self-contained**: No database lookups needed

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Serve frontend HTML |
| `/api/info` | GET | Get game metadata (date, word length, max attempts) |
| `/api/guess` | POST | Submit guess, returns hints + new token |
| `/api/reset` | POST | Reset game, returns fresh token |

## Game Logic (Customizable)

### IGamle Interface

Games implement the `IGamle` interface in [src/gamle.py](../src/gamle.py):

```python
class IGamle(ABC):
    def __init__(self):
        """Initialize with internal challenge cache."""
        self._challenge_cache: dict[str, str] = {}
    
    def get_daily_challenge(self, date_str: str) -> str:
        """
        Public method: Get challenge (cached internally).
        You DON'T override this - it handles caching automatically.
        """
        if date_str not in self._challenge_cache:
            self._challenge_cache[date_str] = self._generate_challenge(date_str)
            # Auto-cleanup: keep only 7 days
        return self._challenge_cache[date_str]
    
    @abstractmethod
    def _generate_challenge(self, date_str: str) -> str:
        """
        Internal method: Generate challenge for a date.
        You MUST implement this - called once per date, then cached.
        Put your expensive generation logic here.
        """
        pass
    
    @abstractmethod
    def check_guess(self, guess: str, secret: str) -> dict[str, Any]:
        """Process a guess and return hints."""
        pass
```

**How it works:**
1. Server calls `game.get_daily_challenge(date)` (public method)
2. If not cached → calls `game._generate_challenge(date)` (your implementation)
3. Result is cached in `self._challenge_cache`
4. Next request for same date → returns cached value instantly

**Why two methods?**
- `get_daily_challenge()`: Handles caching (don't override)
- `_generate_challenge()`: Your expensive logic (must implement)

This separates concerns: base class handles caching, you implement generation.

### Current Implementation

Example in [simple_wordle_game.py](../src/simple_wordle_game.py):

```python
class SimpleWordleGame(IGamle):
    def _generate_challenge(self, date_str: str) -> str:
        """
        Called by get_daily_challenge() when cache miss.
        Generates word using deterministic hash.
        """
        hash_val = int(hashlib.sha256(date_str.encode()).hexdigest(), 16)
        return self.word_list[hash_val % len(self.word_list)]
    
    def check_guess(self, guess: str, secret: str) -> dict:
        """Process guess and return hints."""
        # ... implementation ...
        return {"guess": guess, "hints": [...], "is_correct": bool}

# In main:
game = SimpleWordleGame()
server = GameServer(game)
server.run()
```

**To create your own game:**
1. Create new file (e.g., `my_game.py`)
2. Inherit from `IGamle`
3. Implement `_generate_challenge(date_str)` - your expensive generation logic
4. Implement `check_guess(guess, secret)` - return custom hints
5. Create instance and pass to `GameServer`

**Critical**: Don't override `get_daily_challenge()` - it handles caching. Only implement `_generate_challenge()`.

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
✅ **Efficient**: Challenge cached in memory, generated only once per day  
✅ **Fast**: Subsequent guesses don't regenerate expensive challenges  

## Running the Server

```bash
# Run the simple Wordle demo
uv run src/simple_wordle_game.py

# Or with your own game
uv run src/my_game.py
```

Server starts at: http://127.0.0.1:8000

## Security Considerations

- **Change `SECRET_KEY`** in production
- Use environment variables for secrets
- Consider HTTPS in production
- Rate limiting recommended for `/api/guess` endpoint

## Future Enhancements

- [ ] Add difficulty levels
- [ ] Statistics tracking (win rate, average attempts)
- [ ] Leaderboard (requires database)
- [ ] Share results (emoji grid like Wordle)
- [ ] Multiple game modes
