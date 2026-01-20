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


# API Models (defined at module level for type checking)
class GuessRequest(BaseModel):
    guess: str
    token: str | None = None

class GuessResponse(BaseModel):
    game_state: dict
    token: str
    game_over: bool
    message: str | None = None

GameFactory = Callable[[str], RiddleGame]

class GameServer:
    """Game-agnostic server that works with any RiddleGame implementation."""
    
    def __init__(
        self, 
        games: list[tuple[str, GameFactory]],
        secret_key: str = "your-secret-key-change-this-in-production"
    ):
        """
        Initialize server with multiple games.
        
        Args:
            games: List of (slug, factory) tuples where slug is the URL path (e.g., "wordle-en-5")
                   and factory is a callable that takes a date string and returns a RiddleGame instance
            secret_key: JWT signing key (change in production)
        """
        self.games = {slug: factory for slug, factory in games}
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.app = FastAPI()
        
        # Cache game instances by (slug, date) tuple
        self._game_cache: dict[tuple[str, str], RiddleGame] = {}
        
        # Mount static files directory
        self.app.mount("/static", StaticFiles(directory=str(STATIC_FOLDER_PATH)), name="static")
        
        self._setup_routes()
    
    def get_game_for_date(self, slug: str, date_str: str) -> RiddleGame:
        """
        Get or create a game instance for a specific game slug and date.
        
        Args:
            slug: The game URL slug (e.g., "wordle-en-5")
            date_str: Date in format "YYYY-MM-DD"
            
        Returns:
            RiddleGame instance for that slug and date (cached)
        """
        cache_key = (slug, date_str)
        
        if cache_key not in self._game_cache:
            # Validate slug
            if slug not in self.games:
                raise ValueError(f"Invalid game slug: {slug}")
            
            # Create new game instance for this slug and date
            self._game_cache[cache_key] = self.games[slug](date_str)
            
            # Prevent memory leak: keep only last 7 days per game
            # Remove old entries for this specific slug
            game_dates = [key for key in self._game_cache.keys() if key[0] == slug]
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
    
    def create_token(self, date: str, slug: str, game_state: GameState) -> str:
        """Create JWT token with game state and slug."""
        payload = {
            "date": date,
            "slug": slug,
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
            # Validate slug exists
            slug = payload.get("slug")
            if slug is None or slug not in self.games:
                return None
            return payload
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None
    
    def _setup_routes(self):
        """Setup FastAPI routes dynamically for each game."""
        
        # Root endpoint lists available games
        @self.app.get("/")
        async def read_root():
            """List all available games."""
            games_list = "\n".join([f'<li><a href="/{slug}">{slug}</a></li>' for slug in self.games.keys()])
            return HTMLResponse(
                content=f"<h1>Available Games</h1><ul>{games_list}</ul>"
            )
        
        # Create routes for each game
        for slug in self.games.keys():
            self._create_game_routes(slug)
    
    def _create_game_routes(self, slug: str):
        """Create routes for a specific game slug."""
        
        @self.app.get(f"/{slug}")
        async def game_page():
            """Serve the game page with injected base path."""
            html_file = STATIC_FOLDER_PATH / "index.html"
            try:
                with open(html_file, "r", encoding="utf-8") as f:
                    html_content = f.read()
                    # Inject base path into HTML (before </head> or at start of <body>)
                    base_path_script = f'<script>window.GAME_BASE_PATH = "/{slug}";</script>'
                    if "</head>" in html_content:
                        html_content = html_content.replace("</head>", f"{base_path_script}</head>")
                    else:
                        html_content = base_path_script + html_content
                    return HTMLResponse(content=html_content)
            except FileNotFoundError:
                return HTMLResponse(
                    content="<h1>Game page not found</h1><p>Please create static/index.html</p>",
                    status_code=404
                )
        
        @self.app.get(f"/{slug}/api/info")
        async def get_game_info():
            """Get game information."""
            # Get game instance to retrieve actual word length
            today = self.get_today_date()
            game = self.get_game_for_date(slug, today)
            
            return {
                "date": today,
                "slug": slug,
                "word_length": len(game.secret),
                "max_attempts": 6,
            }
        
        @self.app.post(f"/{slug}/api/guess", response_model=GuessResponse)
        async def make_guess(request: GuessRequest):
            """
            Process a player's guess.
            Returns updated game state in a new JWT token.
            Empty guess validates token without consuming an attempt.
            """
            today = self.get_today_date()
            game_state = None
            
            # Try to restore state from token
            if request.token:
                payload = self.verify_token(request.token)
                if payload and payload.get("date") == today and payload.get("slug") == slug:
                    game_state_dict = payload.get("game_state")
                    if game_state_dict:
                        # Get game instance
                        game = self.get_game_for_date(slug, today)
                        # Deserialize state
                        game_state = game.create_game_state()
                        game_state = type(game_state).from_dict(game_state_dict)
                        
                        # Validate secret hash
                        import hashlib
                        current_hash = hashlib.sha256(game.secret.encode()).hexdigest()
                        
                        if hasattr(game_state, 'secret_hash') and game_state.secret_hash:
                            if game_state.secret_hash != current_hash:
                                # Hash mismatch - game changed, reset
                                game_state = None
            
            # Get game instance
            game = self.get_game_for_date(slug, today)
            
            # If no valid game state, create new one
            if game_state is None:
                game_state = game.create_game_state()
            
            # Handle empty guess (validation only)
            if not request.guess or request.guess.strip() == "":
                new_token = self.create_token(today, slug, game_state)
                
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
                    game_over=game_state.is_game_over(),
                    message=message
                )
            
            # Check if game already over
            if game_state and game_state.is_game_over():
                return GuessResponse(
                    game_state=game_state.to_dict(),
                    token=self.create_token(today, slug, game_state),
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
            new_token = self.create_token(today, slug, game_state)
            
            return GuessResponse(
                game_state=game_state.to_dict(),
                token=new_token,
                game_over=game_state.is_game_over(),
                message=message
            )
        
        @self.app.post(f"/{slug}/api/reset")
        async def reset_game():
            """Reset game and get new token."""
            today = self.get_today_date()
            game = self.get_game_for_date(slug, today)
            new_state = game.create_game_state()
            return {
                "token": self.create_token(today, slug, new_state),
                "message": f"Game reset for today"
            }
    
    def run(self, host: str, port: int):
        """Run the server."""
        import uvicorn
        print("Starting game server...")
        print(f"Number of games: {len(self.games)}")
        print(f"Today's date: {self.get_today_date()}")
        print("\nAvailable games:")
        # Create today's games to show secrets
        for slug in self.games.keys():
            game = self.get_game_for_date(slug, self.get_today_date())
            print(f"  /{slug} - Today's secret (for testing): {game.secret}")
        uvicorn.run(self.app, host=host, port=port)

