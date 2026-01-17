import pytest
import numpy as np
import sys
from os.path import join as pjoin, dirname

# Add src directory to path
sys.path.insert(0, pjoin(dirname(__file__), "..", "src"))

from semantle.main_assistant_semantic import GameAssistant


class TestGameAssistant:
    """Tests for GameAssistant class"""

    @pytest.fixture
    def sample_words(self):
        """Sample words for testing"""
        return ["chat", "chien", "maison", "voiture", "arbre"]

    @pytest.fixture
    def sample_heatmap(self, sample_words):
        """Create a simple heatmap matrix for testing"""
        len(sample_words)
        # Create a symmetric matrix with some correlation values
        matrix = np.array([
            [100, 80, 30, 20, 40],
            [80, 100, 25, 15, 35],
            [30, 25, 100, 60, 50],
            [20, 15, 60, 100, 45],
            [40, 35, 50, 45, 100],
        ], dtype=float)
        return matrix

    @pytest.fixture
    def assistant(self, sample_heatmap, sample_words):
        """Create a GameAssistant instance for testing"""
        return GameAssistant(sample_heatmap, sample_words)

    def test_initialization(self, assistant, sample_words):
        """Test that GameAssistant initializes correctly"""
        assert assistant.all_words == sample_words
        assert assistant.observed_words_score_map == {}
        assert assistant.next_suggestion == sample_words[0]

    def test_add_valid_word(self, assistant):
        """Test adding a valid word and score"""
        suggestion, msg = assistant.add_word_score("chat", 50.0)
        
        assert "chat" in assistant.observed_words_score_map
        assert assistant.observed_words_score_map["chat"] == 50.0
        assert suggestion is not None
        assert "Observed 'chat' with score 50.00" in msg
        assert "Top 10 suggestions:" in msg

    def test_add_invalid_word(self, assistant):
        """Test adding an invalid word not in the list"""
        suggestion, msg = assistant.add_word_score("invalidword", 50.0)
        
        assert suggestion is None
        assert "not in the list" in msg
        assert "invalidword" not in assistant.observed_words_score_map

    def test_compute_sub_matrix(self, assistant):
        """Test sub-matrix computation after adding observations"""
        assistant.add_word_score("chat", 80.0)
        assistant.add_word_score("chien", 75.0)
        
        sub_matrix = assistant.compute_sub_matrix()
        
        # Should have 3 remaining words (rows) and 2 observed words (columns)
        assert sub_matrix.shape == (3, 2)

    def test_compute_word_probabilities(self, assistant):
        """Test word probability computation"""
        assistant.add_word_score("chat", 80.0)
        
        ranked_words, ranked_scores = assistant.compute_word_probabilities()
        
        # Should have 4 remaining words (excluding "chat")
        assert len(ranked_words) == 4
        assert len(ranked_scores) == 4
        assert "chat" not in ranked_words
        # Scores should be in descending order
        assert all(ranked_scores[i] >= ranked_scores[i+1] for i in range(len(ranked_scores)-1))

    def test_multiple_observations(self, assistant):
        """Test adding multiple word observations"""
        assistant.add_word_score("chat", 80.0)
        assistant.add_word_score("chien", 70.0)
        suggestion, msg = assistant.add_word_score("maison", 30.0)
        
        assert len(assistant.observed_words_score_map) == 3
        assert suggestion is not None
        # Should only have 2 remaining words
        ranked_words, _ = assistant.compute_word_probabilities()
        assert len(ranked_words) == 2

    def test_all_words_observed(self, assistant, sample_words):
        """Test behavior when all words have been observed"""
        for word in sample_words:
            suggestion, msg = assistant.add_word_score(word, 50.0)
        
        # Last suggestion should be None as no words remain
        assert suggestion is None
        assert "No more words available" in msg

    def test_next_suggestion_updates(self, assistant):
        """Test that next_suggestion updates after adding words"""
        assistant.add_word_score("chat", 85.0)
        
        # Next suggestion should be different from the observed word
        assert assistant.next_suggestion != "chat"
        # It should be one of the remaining words
        assert assistant.next_suggestion in ["chien", "maison", "voiture", "arbre"]
