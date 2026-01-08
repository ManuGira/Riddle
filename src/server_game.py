"""
Stateless Wordle-like game server using JWT for session management.
Game logic is intentionally simple and can be replaced with your actual game.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import hashlib
from pathlib import Path

app = FastAPI()

# Secret key for JWT signing - CHANGE THIS IN PRODUCTION
SECRET_KEY = "your-secret-key-change-this-in-production"
ALGORITHM = "HS256"

# Load word list for simple game
WORDS_FILE = Path(__file__).parent.parent / "data" / "english_words.txt"


def load_words() -> list[str]:
    """Load words from file and filter to 5-letter words."""
    try:
        with open(WORDS_FILE, "r", encoding="utf-8") as f:
            words = [w.strip().upper() for w in f if len(w.strip()) == 5]
        return [w for w in words if w.isalpha()]
    except FileNotFoundError:
        # Fallback words if file not found
        return ["APPLE", "CRANE", "STOLE", "BEACH", "DREAM", "GLOBE"]


WORD_LIST = load_words()


def get_daily_word(date_str: str) -> str:
    """
    Get the daily word based on date.
    Uses deterministic hash so same date = same word for all players.
    """
    # Hash the date to get consistent index
    hash_val = int(hashlib.sha256(date_str.encode()).hexdigest(), 16)
    index = hash_val % len(WORD_LIST)
    return WORD_LIST[index]


def get_today_date() -> str:
    """Get today's date as string."""
    return datetime.now().strftime("%Y-%m-%d")


def get_midnight_timestamp() -> int:
    """Get timestamp for next midnight (token expiration)."""
    now = datetime.now()
    midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int(midnight.timestamp())


def create_token(state: dict) -> str:
    """Create JWT token with game state."""
    state["exp"] = get_midnight_timestamp()
    return jwt.encode(state, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict | None:
    """Verify and decode JWT token. Returns None if invalid/expired."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Check if token is for today's date
        if payload.get("date") != get_today_date():
            return None
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def new_game_state() -> dict:
    """Create new game state for today."""
    return {
        "date": get_today_date(),
        "guesses": [],
        "attempts": 0,
        "completed": False,
        "won": False,
    }


# ============= GAME LOGIC (REPLACE THIS WITH YOUR GAME) =============

def check_guess(guess: str, secret_word: str) -> dict:
    """
    Simple Wordle-like game logic.
    Returns hints for each letter: 'correct', 'present', or 'absent'.
    
    REPLACE THIS FUNCTION WITH YOUR ACTUAL GAME LOGIC.
    """
    guess = guess.upper().strip()
    secret_word = secret_word.upper()
    
    if len(guess) != len(secret_word):
        raise ValueError(f"Guess must be {len(secret_word)} letters")
    
    hints = []
    for i, letter in enumerate(guess):
        if letter == secret_word[i]:
            hints.append({"letter": letter, "status": "correct"})
        elif letter in secret_word:
            hints.append({"letter": letter, "status": "present"})
        else:
            hints.append({"letter": letter, "status": "absent"})
    
    return {"guess": guess, "hints": hints, "is_correct": guess == secret_word}


# ====================================================================


# API Models
class GuessRequest(BaseModel):
    guess: str
    token: str | None = None


class GuessResponse(BaseModel):
    result: dict
    state: dict
    token: str
    game_over: bool
    message: str | None = None


# API Endpoints
@app.get("/")
async def read_root():
    """Serve the main game page."""
    html_file = Path(__file__).parent.parent / "static" / "index.html"
    try:
        with open(html_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Game page not found</h1><p>Please create static/index.html</p>",
            status_code=404
        )


@app.get("/api/info")
async def get_game_info():
    """Get general game information (no spoilers)."""
    return {
        "date": get_today_date(),
        "word_length": 5,
        "max_attempts": 6,
    }


@app.post("/api/guess", response_model=GuessResponse)
async def make_guess(request: GuessRequest):
    """
    Process a player's guess.
    Returns updated game state in a new JWT token.
    """
    # Verify existing token or create new game
    if request.token:
        state = verify_token(request.token)
        if state is None:
            # Token expired or invalid, start new game
            state = new_game_state()
    else:
        state = new_game_state()
    
    # Check if game already completed
    if state.get("completed"):
        return GuessResponse(
            result={},
            state=state,
            token=create_token(state),
            game_over=True,
            message="Game already completed for today!"
        )
    
    # Check max attempts (6 like Wordle)
    if state["attempts"] >= 6:
        state["completed"] = True
        state["won"] = False
        return GuessResponse(
            result={},
            state=state,
            token=create_token(state),
            game_over=True,
            message=f"Game over! The word was: {get_daily_word(state['date'])}"
        )
    
    # Get today's secret word
    secret_word = get_daily_word(state["date"])
    
    # Process the guess
    try:
        result = check_guess(request.guess, secret_word)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Update state
    state["guesses"].append(result)
    state["attempts"] += 1
    
    # Check if won
    if result["is_correct"]:
        state["completed"] = True
        state["won"] = True
        message = f"🎉 Congratulations! You won in {state['attempts']} attempts!"
        game_over = True
    elif state["attempts"] >= 6:
        state["completed"] = True
        state["won"] = False
        message = f"Game over! The word was: {secret_word}"
        game_over = True
    else:
        message = f"Attempt {state['attempts']}/6"
        game_over = False
    
    # Create new token with updated state
    new_token = create_token(state)
    
    return GuessResponse(
        result=result,
        state=state,
        token=new_token,
        game_over=game_over,
        message=message
    )


@app.post("/api/reset")
async def reset_game():
    """Reset game and get new token."""
    state = new_game_state()
    return {
        "token": create_token(state),
        "message": "Game reset for today"
    }


if __name__ == "__main__":
    import uvicorn
    print(f"Starting server...")
    print(f"Today's secret word (for testing): {get_daily_word(get_today_date())}")
    print(f"Available words: {len(WORD_LIST)}")
    uvicorn.run(app, host="127.0.0.1", port=8000)
