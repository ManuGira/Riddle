"""
Stateless Wordle-like game server using JWT for session management.
Completely game-agnostic - works with any RiddleGame implementation.
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
from pathlib import Path

from riddle import STATIC_FOLDER_PATH
from .riddle_game import RiddleGame
from .game_state import GameState
from typing import Callable


class GameServer:
    """Game-agnostic server that works with any RiddleGame implementation."""
    
    def __init__(
        self, 
        game_factory: Callable[[str], RiddleGame],
        secret_key: str = "your-secret-key-change-this-in-production"
    ):
        """
        Initialize server with a game factory.
        
        Args:
            game_factory: Callable that takes a date string and returns a RiddleGame instance
            secret_key: JWT signing key (change in production)
        """
        self.game_factory = game_factory
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.app = FastAPI()
        
        # Cache game instances by date (max 7 days)
        self._game_cache: dict[str, RiddleGame] = {}
        
        self._setup_routes()
    
    def get_game_for_date(self, date_str: str) -> RiddleGame:
        """
        Get or create a game instance for a specific date.
        
        Args:
            date_str: Date in format "YYYY-MM-DD"
            
        Returns:
            RiddleGame instance for that date (cached)
        """
        if date_str not in self._game_cache:
            # Create new game instance for this date
            self._game_cache[date_str] = self.game_factory(date_str)
            
            # Prevent memory leak: keep only last 7 days
            if len(self._game_cache) > 7:
                oldest_date = min(self._game_cache.keys())
                del self._game_cache[oldest_date]
        
        return self._game_cache[date_str]
    
    def get_today_date(self) -> str:
        """Get today's date as string."""
        return datetime.now().strftime("%Y-%m-%d")
    
    def get_midnight_timestamp(self) -> int:
        """Get timestamp for next midnight (token expiration)."""
        now = datetime.now()
        midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return int(midnight.timestamp())
    
    def create_token(self, date: str, game_state: GameState) -> str:
        """Create JWT token with game state."""
        payload = {
            "date": date,
            "game_state": game_state.to_dict()
        }
        payload["exp"] = self.get_midnight_timestamp()
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
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
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        # API Models
        class GuessRequest(BaseModel):
            guess: str
            token: str | None = None
        
        class GuessResponse(BaseModel):
            game_state: dict
            token: str
            game_over: bool
            message: str | None = None
        
        @self.app.get("/")
        async def read_root():
            """Serve the main game page."""
            html_file = STATIC_FOLDER_PATH / "index.html"
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
            today = self.get_today_date()
            game = self.get_game_for_date(today)
            
            # Verify existing token or create new game
            game_state = None
            if request.token:
                payload = self.verify_token(request.token)
                if payload and payload.get("date") == today:
                    # Reconstruct GameState from JWT
                    game_state_dict = payload.get("game_state")
                    if game_state_dict:
                        # Get state class from game and deserialize
                        game_state = game.create_game_state()
                        game_state = type(game_state).from_dict(game_state_dict)
            
            # Check if game already over
            if game_state and game_state.is_game_over():
                return GuessResponse(
                    game_state=game_state.to_dict(),
                    token=self.create_token(today, game_state),
                    game_over=True,
                    message="Game already completed for today!"
                )
            
            # Process the guess
            try:
                game_state = game.check_guess(request.guess, game_state)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            
            # Generate message
            if game_state.is_game_over():
                if hasattr(game_state, 'won') and game_state.won:
                    message = f"🎉 Congratulations! You won in {game_state.attempts} attempts!"
                else:
                    message = f"Game over! The word was: {game.secret}"
            else:
                message = f"Attempt {game_state.attempts}/{game_state.max_attempts}"
            
            # Create new token with updated state
            new_token = self.create_token(today, game_state)
            
            return GuessResponse(
                game_state=game_state.to_dict(),
                token=new_token,
                game_over=game_state.is_game_over(),
                message=message
            )
        
        @self.app.post("/api/reset")
        async def reset_game():
            """Reset game and get new token."""
            today = self.get_today_date()
            game = self.get_game_for_date(today)
            new_state = game.create_game_state()
            return {
                "token": self.create_token(today, new_state),
                "message": "Game reset for today"
            }
    
    def run(self, host: str = "127.0.0.1", port: int = 8000):
        """Run the server."""
        import uvicorn
        print(f"Starting game server...")
        print(f"Game factory ready")
        print(f"Today's date: {self.get_today_date()}")
        # Create today's game to show secret
        today_game = self.get_game_for_date(self.get_today_date())
        print(f"Today's secret (for testing): {today_game.secret}")
        uvicorn.run(self.app, host=host, port=port)

