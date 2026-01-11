"""
Stateless Wordle-like game server using JWT for session management.
Completely game-agnostic - works with any IGamle implementation.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
from pathlib import Path
from riddle_interface import IRiddle


class GameServer:
    """Game-agnostic server that works with any IGamle implementation."""
    
    def __init__(self, game: IRiddle, secret_key: str = "your-secret-key-change-this-in-production"):
        """
        Initialize server with a game instance.
        
        Args:
            game: Any object implementing the IGamle interface
            secret_key: JWT signing key (change in production)
        """
        self.game = game
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.app = FastAPI()
        self._setup_routes()
    
    def get_today_date(self) -> str:
        """Get today's date as string."""
        return datetime.now().strftime("%Y-%m-%d")
    
    def get_midnight_timestamp(self) -> int:
        """Get timestamp for next midnight (token expiration)."""
        now = datetime.now()
        midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return int(midnight.timestamp())
    
    def create_token(self, state: dict) -> str:
        """Create JWT token with game state."""
        state["exp"] = self.get_midnight_timestamp()
        return jwt.encode(state, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> dict | None:
        """Verify and decode JWT token. Returns None if invalid/expired."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            # Check if token is for today's date
            if payload.get("date") != self.get_today_date():
                return None
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
    
    def new_game_state(self) -> dict:
        """Create new game state for today."""
        return {
            "date": self.get_today_date(),
            "guesses": [],
            "attempts": 0,
            "completed": False,
            "won": False,
        }
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
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
        
        @self.app.get("/")
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
        
        @self.app.get("/api/info")
        async def get_game_info():
            """Get general game information (no spoilers)."""
            return {
                "date": self.get_today_date(),
                "word_length": 5,
                "max_attempts": 6,
            }
        
        @self.app.post("/api/guess", response_model=GuessResponse)
        async def make_guess(request: GuessRequest):
            """
            Process a player's guess.
            Returns updated game state in a new JWT token.
            """
            # Verify existing token or create new game
            if request.token:
                state = self.verify_token(request.token)
                if state is None:
                    # Token expired or invalid, start new game
                    state = self.new_game_state()
            else:
                state = self.new_game_state()
            
            # Check if game already completed
            if state.get("completed"):
                return GuessResponse(
                    result={},
                    state=state,
                    token=self.create_token(state),
                    game_over=True,
                    message="Game already completed for today!"
                )
            
            # Check max attempts (6 like Wordle)
            if state["attempts"] >= 6:
                state["completed"] = True
                state["won"] = False
                # Use game instance to get cached challenge
                secret_word = self.game.get_daily_challenge(state["date"])
                return GuessResponse(
                    result={},
                    state=state,
                    token=self.create_token(state),
                    game_over=True,
                    message=f"Game over! The word was: {secret_word}"
                )
            
            # Get today's secret word (cached inside game instance)
            secret_word = self.game.get_daily_challenge(state["date"])
            
            # Process the guess using game instance
            try:
                result = self.game.check_guess(request.guess, secret_word)
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
            new_token = self.create_token(state)
            
            return GuessResponse(
                result=result,
                state=state,
                token=new_token,
                game_over=game_over,
                message=message
            )
        
        @self.app.post("/api/reset")
        async def reset_game():
            """Reset game and get new token."""
            state = self.new_game_state()
            return {
                "token": self.create_token(state),
                "message": "Game reset for today"
            }
    
    def run(self, host: str = "127.0.0.1", port: int = 8000):
        """Run the server."""
        import uvicorn
        print(f"Starting game server...")
        print(f"Game type: {type(self.game).__name__}")
        print(f"Today's date: {self.get_today_date()}")
        uvicorn.run(self.app, host=host, port=port)

