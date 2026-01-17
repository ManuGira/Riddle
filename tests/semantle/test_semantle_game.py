import pytest
import numpy as np
import sys
from os.path import join as pjoin, dirname
from unittest.mock import Mock

# Add src directory to path
sys.path.insert(0, pjoin(dirname(__file__), "..", "src"))

from semantle.main_semantle_game import SemanticGame


class TestSemanticGame:
    """Tests for SemanticGame class"""

    @pytest.fixture
    def mock_model(self):
        """Create a mock word2vec model"""
        model = Mock()
        # Define similarity behavior: high for same word, lower for others
        def similarity_func(word1, word2):
            if word1 == word2:
                return 1.0
            # Simple similarity based on word length difference
            return max(0.1, 1.0 - abs(len(word1) - len(word2)) * 0.1)
        
        model.similarity.side_effect = similarity_func
        return model

    @pytest.fixture
    def sample_words(self):
        """Sample words for testing"""
        return ["chat", "chien", "maison", "voiture", "arbre"]

    @pytest.fixture
    def game(self, mock_model, sample_words):
        """Create a SemanticGame instance for testing"""
        np.random.seed(42)  # For reproducible tests
        return SemanticGame(mock_model, sample_words)

    def test_initialization(self, game, sample_words):
        """Test that SemanticGame initializes correctly"""
        assert game.available_words == sample_words
        assert game.secret_word in sample_words
        assert game.attempts == 0
        assert game.observed == {}
        assert game.game_on is True

    def test_valid_guess(self, game, mock_model):
        """Test making a valid guess"""
        score, msg = game.play_turn("chat")
        
        assert score is not None
        assert isinstance(score, float)
        assert msg is not None
        assert "chat" in game.observed
        assert game.attempts == 1

    def test_invalid_guess(self, game):
        """Test guessing a word not in available words"""
        score, msg = game.play_turn("invalidword")
        
        assert score is None
        assert "not in the list" in msg
        assert "invalidword" not in game.observed
        assert game.attempts == 0  # Attempt not counted

    def test_correct_guess(self, game):
        """Test guessing the correct word"""
        secret = game.secret_word
        score, msg = game.play_turn(secret)
        
        assert score == pytest.approx(100.0)
        assert "Congratulations" in msg
        assert secret in msg
        assert game.game_on is False

    def test_multiple_guesses(self, game):
        """Test making multiple guesses"""
        game.play_turn("chat")
        game.play_turn("chien")
        score, msg = game.play_turn("maison")
        
        assert len(game.observed) == 3
        assert game.attempts == 3
        # All three words should appear in message
        assert "chat" in msg
        assert "chien" in msg
        assert "maison" in msg

    def test_observed_tracking(self, game):
        """Test that observed words track attempt number and score"""
        game.play_turn("chat")
        game.play_turn("chien")
        
        assert "chat" in game.observed
        assert "chien" in game.observed
        # Each observed entry should have (attempt, score) tuple
        attempt, score = game.observed["chat"]
        assert attempt == 0
        assert isinstance(score, float)

    def test_duplicate_guess(self, game):
        """Test guessing the same word twice"""
        score1, msg1 = game.play_turn("chat")
        score2, msg2 = game.play_turn("chat")
        
        # Should still be recorded only once in observed
        assert len(game.observed) == 1
        # But attempts should increment
        assert game.attempts == 2
        # Original attempt number should be preserved
        attempt, _ = game.observed["chat"]
        assert attempt == 0

    def test_score_calculation(self, game, mock_model):
        """Test that score is calculated correctly from model similarity"""
        guess = "chat"
        score, _ = game.play_turn(guess)
        
        # Score should be 100 * similarity
        expected_similarity = mock_model.similarity(guess, game.secret_word)
        expected_score = 100 * expected_similarity
        assert score == pytest.approx(expected_score)

    def test_game_continues_after_wrong_guess(self, game):
        """Test that game continues after an incorrect guess"""
        # Make a guess that's not the secret word
        wrong_guesses = [w for w in game.available_words if w != game.secret_word]
        game.play_turn(wrong_guesses[0])
        
        assert game.game_on is True
        assert game.attempts == 1

    def test_message_format(self, game):
        """Test that return message has expected format"""
        score, msg = game.play_turn("chat")
        
        # Message should include attempt number, word, and score
        assert "0 chat:" in msg
        assert "current_score" in msg
        assert "----" in msg
