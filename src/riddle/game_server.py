"""
Stateless Wordle-like game server using JWT for session management.
Completely game-agnostic - works with any RiddleGame implementation.
Supports multiple game instances simultaneously (e.g., French and English Wordle).
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt

from riddle import STATIC_FOLDER_PATH, RiddleGame, GameState
from typing import Callable


class GameServer:
    """Game-agnostic server that works with any RiddleGame implementation."""
    
    def __init__(
        self, 
        game_factories: list[Callable[[str], RiddleGame]],
        secret_key: str = "your-secret-key-change-this-in-production"
    ):
        """
        Initialize server with multiple game factories.
        
        Args:
            game_factories: List of callables that take a date string and return a RiddleGame instance
            secret_key: JWT signing key (change in production)
        """
        self.game_factories = game_factories
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.app = FastAPI()
        
        # Cache game instances by (game_id, date) tuple
        self._game_cache: dict[tuple[int, str], RiddleGame] = {}
        
        # Counter for generating game IDs
        self._game_id_counter = 0
        
        # Mount static files directory
        self.app.mount("/static", StaticFiles(directory=str(STATIC_FOLDER_PATH)), name="static")
        
        self._setup_routes()
    
    def get_next_game_id(self) -> int:
        """Generate a unique game ID."""
        game_id = self._game_id_counter
        self._game_id_counter += 1
        return game_id
    
    def get_game_for_date(self, game_id: int, date_str: str) -> RiddleGame:
        """
        Get or create a game instance for a specific game ID and date.
        
        Args:
            game_id: The game instance ID
            date_str: Date in format "YYYY-MM-DD"
            
        Returns:
            RiddleGame instance for that game ID and date (cached)
        """
        cache_key = (game_id, date_str)
        
        if cache_key not in self._game_cache:
            # Validate game_id
            if game_id < 0 or game_id >= len(self.game_factories):
                raise ValueError(f"Invalid game_id: {game_id}")
            
            # Create new game instance for this game_id and date
            self._game_cache[cache_key] = self.game_factories[game_id](date_str)
            
            # Prevent memory leak: keep only last 7 days per game
            # Remove old entries for this specific game_id
            game_dates = [key for key in self._game_cache.keys() if key[0] == game_id]
            if len(game_dates) > 7:
                oldest_key = min(game_dates, key=lambda k: k[1])
                del self._game_cache[oldest_key]
        
        return self._game_cache[cache_key]
    
    def get_today_date(self) -> str:
        """Get today's date as string."""
        return datetime.now().strftime("%Y-%m-%d")
    
    def get_midnight_timestamp(self) -> int:
        """Get timestamp for next midnight (token expiration)."""
        now = datetime.now()
        midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return int(midnight.timestamp())
    
    def create_token(self, date: str, game_id: int, game_state: GameState) -> str:
        """Create JWT token with game state and game ID."""
        payload = {
            "date": date,
            "game_id": game_id,
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
            # Validate game_id exists
            game_id = payload.get("game_id")
            if game_id is None or game_id < 0 or game_id >= len(self.game_factories):
                return None
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        # API Models
        class GuessRequest(BaseModel):
            guess: str
            game_id: int | None = None  # Game ID for new game, or extracted from token
            token: str | None = None
        
        class GuessResponse(BaseModel):
            game_state: dict
            token: str
            game_id: int
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
            """Get general game information for all available games."""
            return {
                "date": self.get_today_date(),
                "games_count": len(self.game_factories),
                "word_length": 5,
                "max_attempts": 6,
            }
        
        @self.app.post("/api/guess", response_model=GuessResponse)
        async def make_guess(request: GuessRequest):
            """
            Process a player's guess for a specific game.
            Returns updated game state in a new JWT token.
            Empty guess validates token without consuming an attempt.
            """
            today = self.get_today_date()
            
            # Determine game_id: from token if present, otherwise from request
            game_id = None
            game_state = None
            
            if request.token:
                payload = self.verify_token(request.token)
                if payload and payload.get("date") == today:
                    game_id = payload.get("game_id")
                    # Reconstruct GameState from JWT
                    game_state_dict = payload.get("game_state")
                    if game_state_dict and game_id is not None:
                        # Get game instance
                        game = self.get_game_for_date(game_id, today)
                        # Get state class from game and deserialize
                        game_state = game.create_game_state()
                        game_state = type(game_state).from_dict(game_state_dict)
                        
                        # Validate secret hash
                        import hashlib
                        current_hash = hashlib.sha256(game.secret.encode()).hexdigest()
                        
                        if hasattr(game_state, 'secret_hash') and game_state.secret_hash:
                            if game_state.secret_hash != current_hash:
                                # Hash mismatch - game changed, reset
                                game_state = None
            
            # If no valid game_id from token, use request.game_id or default to 0
            if game_id is None:
                game_id = request.game_id if request.game_id is not None else 0
                
            # Validate game_id
            if game_id < 0 or game_id >= len(self.game_factories):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid game_id: {game_id}. Must be between 0 and {len(self.game_factories) - 1}"
                )
            
            # Get game instance
            game = self.get_game_for_date(game_id, today)
            
            # If no valid game state, create new one
            if game_state is None:
                game_state = game.create_game_state()
            
            # Handle empty guess (validation only - doesn't consume attempt)
            if not request.guess or request.guess.strip() == "":
                # Just return current state with fresh token
                new_token = self.create_token(today, game_id, game_state)
                
                if hasattr(game_state, 'attempts') and game_state.attempts == 0:
                    message = "Ready to play!"
                elif game_state.is_game_over():
                    if hasattr(game_state, 'won') and game_state.won:
                        attempts_msg = f" in {game_state.attempts} attempts" if hasattr(game_state, 'attempts') else ""
                        message = f"🎉 Game completed! You won{attempts_msg}!"
                    else:
                        message = f"Game over! The word was: {game.secret}"
                else:
                    if hasattr(game_state, 'attempts') and hasattr(game_state, 'max_attempts'):
                        message = f"Attempt {game_state.attempts}/{game_state.max_attempts}"
                    else:
                        message = "Game in progress"
                
                return GuessResponse(
                    game_state=game_state.to_dict(),
                    token=new_token,
                    game_id=game_id,
                    game_over=game_state.is_game_over(),
                    message=message
                )
            
            # Check if game already over
            if game_state and game_state.is_game_over():
                return GuessResponse(
                    game_state=game_state.to_dict(),
                    token=self.create_token(today, game_id, game_state),
                    game_id=game_id,
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
                    attempts_msg = f" in {game_state.attempts} attempts" if hasattr(game_state, 'attempts') else ""
                    message = f"🎉 Congratulations! You won{attempts_msg}!"
                else:
                    message = f"Game over! The word was: {game.secret}"
            else:
                if hasattr(game_state, 'attempts') and hasattr(game_state, 'max_attempts'):
                    message = f"Attempt {game_state.attempts}/{game_state.max_attempts}"
                else:
                    message = "Game in progress"
            
            # Create new token with updated state
            new_token = self.create_token(today, game_id, game_state)
            
            return GuessResponse(
                game_state=game_state.to_dict(),
                token=new_token,
                game_id=game_id,
                game_over=game_state.is_game_over(),
                message=message
            )
        
        @self.app.post("/api/reset")
        async def reset_game(game_id: int = 0):
            """Reset game for a specific game ID and get new token."""
            # Validate game_id
            if game_id < 0 or game_id >= len(self.game_factories):
                raise HTTPException(
                    status_code=400, 
                    detail=f"Invalid game_id: {game_id}. Must be between 0 and {len(self.game_factories) - 1}"
                )
            
            today = self.get_today_date()
            game = self.get_game_for_date(game_id, today)
            new_state = game.create_game_state()
            return {
                "token": self.create_token(today, game_id, new_state),
                "game_id": game_id,
                "message": f"Game {game_id} reset for today"
            }
    
    def run(self, host: str, port: int):
        """Run the server."""
        import uvicorn
        print("Starting game server...")
        print(f"Number of game factories: {len(self.game_factories)}")
        print(f"Today's date: {self.get_today_date()}")
        # Create today's games to show secrets
        for i, factory in enumerate(self.game_factories):
            game = self.get_game_for_date(i, self.get_today_date())
            print(f"Game {i} - Today's secret (for testing): {game.secret}")
        uvicorn.run(self.app, host=host, port=port)

