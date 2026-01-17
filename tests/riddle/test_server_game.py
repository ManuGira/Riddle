"""
Unit tests for GameServer.
"""
import sys
from pathlib import Path
from unittest.mock import Mock
from datetime import datetime, timedelta

import pytest

from riddle.game_server import GameServer
from riddle.riddle_game import RiddleGame
from riddle.game_state import GameState


class MockGameState(GameState):
    """Mock game state for testing."""
    
    def __init__(self, attempts=0, game_over=False):
        self.attempts = attempts
        self.game_over = game_over
    
    def to_dict(self):
        return {"attempts": self.attempts, "game_over": self.game_over}
    
    @classmethod
    def from_dict(cls, data):
        return cls(attempts=data.get("attempts", 0), game_over=data.get("game_over", False))
    
    def is_game_over(self):
        return self.game_over


class TestGameServer:
    """Test GameServer functionality."""
    
    @pytest.fixture
    def mock_game_factory(self):
        """Create a mock game factory."""
        def factory(date_str):
            game = Mock(spec=RiddleGame)
            game.secret = "CRANE"
            # Configure mock methods properly
            game.create_game_state = Mock(return_value=MockGameState())
            game.check_guess = Mock(return_value=MockGameState(attempts=1))
            return game
        return factory
    
    @pytest.fixture
    def server(self, mock_game_factory):
        """Create GameServer instance."""
        return GameServer(mock_game_factory, secret_key="test-secret-key")
    
    def test_server_initialization(self, server):
        """Test server initializes correctly."""
        assert server.game_factory is not None
        assert server.secret_key == "test-secret-key"
        assert server.algorithm == "HS256"
        assert len(server._game_cache) == 0
    
    def test_game_caching(self, server):
        """Test game instances are cached by date."""
        game1 = server.get_game_for_date("2026-01-12")
        game2 = server.get_game_for_date("2026-01-12")
        game3 = server.get_game_for_date("2026-01-13")
        
        assert game1 is game2  # Same instance for same date
        assert game1 is not game3  # Different instance for different date
        assert len(server._game_cache) == 2
    
    def test_cache_limit(self, server):
        """Test cache keeps only last 7 days."""
        for i in range(10):
            server.get_game_for_date(f"2026-01-{i+1:02d}")
        
        assert len(server._game_cache) <= 7
    
    def test_get_today_date(self, server):
        """Test getting today's date string."""
        today = server.get_today_date()
        expected = datetime.now().strftime("%Y-%m-%d")
        assert today == expected
    
    def test_midnight_timestamp(self, server):
        """Test midnight timestamp is in the future."""
        midnight = server.get_midnight_timestamp()
        now = int(datetime.now().timestamp())
        
        assert midnight > now
        
        # Should be less than 24 hours away
        assert midnight - now < 86400
    
    def test_token_creation_and_verification(self, server, monkeypatch):
        """Test JWT token creation and verification."""
        # Mock today's date to match token date
        monkeypatch.setattr(server, 'get_today_date', lambda: "2026-01-12")
        
        state = MockGameState(attempts=3)
        date = "2026-01-12"
        
        token = server.create_token(date, state)
        assert isinstance(token, str)
        
        payload = server.verify_token(token)
        assert payload is not None
        assert payload["date"] == date
        assert payload["game_state"]["attempts"] == 3
    
    def test_token_expiration(self, server):
        """Test expired token returns None."""
        state = MockGameState()
        
        # Create token with past expiration
        import jwt
        payload = {"date": "2026-01-01", "game_state": state.to_dict(), "exp": 0}
        expired_token = jwt.encode(payload, server.secret_key, algorithm=server.algorithm)
        
        result = server.verify_token(expired_token)
        assert result is None
    
    def test_token_wrong_date(self, server):
        """Test token with wrong date returns None."""
        state = MockGameState()
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        token = server.create_token(yesterday, state)
        result = server.verify_token(token)
        
        assert result is None  # Token for yesterday, not today
