import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from riddle.common import (compute_correlation_matrix, compute_distance_matrix,
                           compute_heatmap_matrix, compute_similarity_matrix,
                           load_most_frequent_words, compute_letter_frequency,
                           compute_positional_letter_frequency,
                           compute_positional_letter_entropy)


class TestLoadMostFrequentWords:
    """Tests for load_most_frequent_words function"""

    @pytest.fixture
    def temp_frequency_file(self):
        """Create a temporary frequency file for testing"""
        content = """chat
chien
maison
œuvre
l'hiver
un
voiture
arbre
où
a
plusieurs
"""
        # Create temp directory and file with expected name
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir) / "french_words_5000.txt"
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(content)
        yield temp_dir  # Return directory, not file path
        # Cleanup
        os.unlink(temp_path)
        os.rmdir(temp_dir)

    def test_load_all_words(self, temp_frequency_file):
        """Test loading all words without N limit"""
        with patch('riddle.common.DATA_FOLDER_PATH', Path(temp_frequency_file)):
            words = load_most_frequent_words(N=None)
            
            # Should exclude: œuvre (has œ->oe but that's fine), l'hiver (apostrophe), 
            # un, où, a (length<2), plusieurs (UNKNOWN_WORDS)
            assert "chat" in words
            assert "chien" in words
            assert "maison" in words
            assert "oeuvre" in words  # œ replaced with oe
            assert "l'hiver" not in words  # has apostrophe
            assert "un" not in words  # in UNKNOWN_WORDS
            assert "où" not in words  # in UNKNOWN_WORDS

    def test_load_with_limit(self, temp_frequency_file):
        """Test loading with N limit"""
        with patch('riddle.common.DATA_FOLDER_PATH', Path(temp_frequency_file)):
            words = load_most_frequent_words(N=3)
            
            assert len(words) == 3

    def test_load_with_model_filter(self, temp_frequency_file):
        """Test loading with model filtering"""
        mock_model = Mock()
        mock_model.key_to_index = {"chat": 0, "chien": 1, "maison": 2}
        
        with patch('riddle.common.DATA_FOLDER_PATH', Path(temp_frequency_file)):
            words = load_most_frequent_words(N=None, model=mock_model)
            
            # Only words in model should be included
            assert "chat" in words
            assert "chien" in words
            assert "maison" in words
            assert "voiture" not in words  # not in model
            assert "arbre" not in words  # not in model

    def test_special_character_replacement(self, temp_frequency_file):
        """Test that œ is replaced with oe"""
        with patch('riddle.common.DATA_FOLDER_PATH', Path(temp_frequency_file)):
            words = load_most_frequent_words(N=None)
            
            assert "oeuvre" in words
            assert "œuvre" not in words


class TestMatrixComputations:
    """Tests for matrix computation functions"""

    @pytest.fixture
    def mock_model(self):
        """Create a mock model with vectors"""
        model = Mock()
        # Create simple 2D vectors for testing
        model.key_to_index = {"chat": 0, "chien": 1, "maison": 2}
        model.vectors = np.array([
            [1.0, 0.0],  # chat
            [0.8, 0.6],  # chien
            [0.0, 1.0],  # maison
        ])
        
        # Mock similarity function
        def similarity_func(w1, w2):
            if w1 == w2:
                return 1.0
            if {w1, w2} == {"chat", "chien"}:
                return 0.8
            if {w1, w2} == {"chat", "maison"}:
                return 0.0
            if {w1, w2} == {"chien", "maison"}:
                return 0.6
            return 0.5
        
        model.similarity.side_effect = similarity_func
        return model

    @pytest.fixture
    def test_words(self):
        """Words for testing"""
        return ["chat", "chien", "maison"]

    def test_compute_correlation_matrix_shape(self, mock_model, test_words):
        """Test that correlation matrix has correct shape"""
        matrix = compute_correlation_matrix(mock_model, test_words)
        
        assert matrix.shape == (3, 3)

    def test_compute_correlation_matrix_diagonal(self, mock_model, test_words):
        """Test that diagonal values are 1 (word with itself)"""
        matrix = compute_correlation_matrix(mock_model, test_words)
        
        for i in range(len(test_words)):
            assert matrix[i, i] == pytest.approx(1.0)

    def test_compute_correlation_matrix_symmetric(self, mock_model, test_words):
        """Test that correlation matrix is symmetric"""
        matrix = compute_correlation_matrix(mock_model, test_words)
        
        assert np.allclose(matrix, matrix.T)

    def test_compute_distance_matrix_shape(self, mock_model, test_words):
        """Test that distance matrix has correct shape"""
        matrix = compute_distance_matrix(mock_model, test_words)
        
        assert matrix.shape == (3, 3)

    def test_compute_distance_matrix_diagonal(self, mock_model, test_words):
        """Test that diagonal values are 0 (distance to self)"""
        matrix = compute_distance_matrix(mock_model, test_words)
        
        for i in range(len(test_words)):
            assert matrix[i, i] == pytest.approx(0.0)

    def test_compute_distance_matrix_symmetric(self, mock_model, test_words):
        """Test that distance matrix is symmetric"""
        matrix = compute_distance_matrix(mock_model, test_words)
        
        assert np.allclose(matrix, matrix.T)

    def test_compute_distance_matrix_positive(self, mock_model, test_words):
        """Test that all distances are non-negative"""
        matrix = compute_distance_matrix(mock_model, test_words)
        
        assert np.all(matrix >= 0)

    def test_compute_similarity_matrix_shape(self, mock_model, test_words):
        """Test that similarity matrix has correct shape"""
        matrix = compute_similarity_matrix(mock_model, test_words)
        
        assert matrix.shape == (3, 3)

    def test_compute_similarity_matrix_diagonal(self, mock_model, test_words):
        """Test that diagonal values are 1 (similarity with self)"""
        matrix = compute_similarity_matrix(mock_model, test_words)
        
        for i in range(len(test_words)):
            assert matrix[i, i] == pytest.approx(1.0)

    def test_compute_similarity_matrix_uses_model(self, mock_model, test_words):
        """Test that similarity matrix uses model.similarity method"""
        matrix = compute_similarity_matrix(mock_model, test_words)
        
        # Check that model.similarity was called
        assert mock_model.similarity.called
        # Verify specific values from mock
        assert matrix[0, 1] == pytest.approx(0.8)  # chat-chien

    def test_compute_heatmap_matrix_scale(self, mock_model, test_words):
        """Test that heatmap matrix scales similarity by 100"""
        similarity_matrix = compute_similarity_matrix(mock_model, test_words)
        heatmap_matrix = compute_heatmap_matrix(mock_model, test_words)
        
        assert np.allclose(heatmap_matrix, similarity_matrix * 100)

    def test_compute_heatmap_matrix_diagonal(self, mock_model, test_words):
        """Test that heatmap diagonal values are 100"""
        matrix = compute_heatmap_matrix(mock_model, test_words)
        
        for i in range(len(test_words)):
            assert matrix[i, i] == pytest.approx(100.0)

    def test_matrices_with_filtered_words(self, mock_model):
        """Test matrix computation with words not all in model"""
        words = ["chat", "chien", "unknown", "maison"]
        
        # Should only use words in model
        matrix = compute_correlation_matrix(mock_model, words)
        assert matrix.shape == (3, 3)  # 3 words in model, not 4

    def test_empty_word_list(self, mock_model):
        """Test matrix computation with empty word list"""
        matrix = compute_correlation_matrix(mock_model, [])
        
        assert matrix.shape == (0, 0)

class TestLetterFrequency:
    """Tests for letter frequency computation functions"""
    
    def test_compute_letter_frequency_basic(self):
        """Test basic letter frequency computation"""
        words = ['abc', 'def', 'aeg']
        freq = compute_letter_frequency(words)
        
        # Each word contributes 3 distinct letters = 9 total
        # 'a' appears in 2 words, 'e' in 2, 'g' in 1
        # Total unique letters counted = 3 + 3 + 3 = 9
        assert freq['a'] == pytest.approx(2/9)
        assert freq['e'] == pytest.approx(2/9)
        assert freq['g'] == pytest.approx(1/9)
        assert freq['b'] == pytest.approx(1/9)
    
    def test_compute_positional_letter_frequency_basic(self):
        """Test position-specific letter frequency"""
        words = ['abc', 'adc', 'bef']
        freq_maps = compute_positional_letter_frequency(words)
        
        # Should return list of 3 dicts (one per position)
        assert len(freq_maps) == 3
        
        # Position 0: 'a' appears in 2 words, 'b' in 1 word
        assert freq_maps[0]['a'] == pytest.approx(2/3)
        assert freq_maps[0]['b'] == pytest.approx(1/3)
        
        # Position 1: 'b' in 1, 'd' in 1, 'e' in 1
        assert freq_maps[1]['b'] == pytest.approx(1/3)
        assert freq_maps[1]['d'] == pytest.approx(1/3)
        assert freq_maps[1]['e'] == pytest.approx(1/3)
        
        # Position 2: 'c' in 2, 'f' in 1
        assert freq_maps[2]['c'] == pytest.approx(2/3)
        assert freq_maps[2]['f'] == pytest.approx(1/3)
    
    def test_compute_positional_letter_frequency_different_lengths(self):
        """Test with words of different lengths"""
        words = ['ab', 'abc', 'abcd']
        freq_maps = compute_positional_letter_frequency(words)
        
        # Should use max length = 4
        assert len(freq_maps) == 4
        
        # Position 0: all 3 words have 'a'
        assert freq_maps[0]['a'] == pytest.approx(1.0)
        
        # Position 3: only 1 word has position 3 ('d')
        assert freq_maps[3]['d'] == pytest.approx(1.0)
        assert len(freq_maps[3]) == 1  # Only 'd' exists at position 3
    
    def test_compute_positional_letter_frequency_empty(self):
        """Test with empty word list"""
        words = []
        freq_maps = compute_positional_letter_frequency(words)
        
        assert freq_maps == []
    
    def test_compute_positional_letter_entropy_basic(self):
        """Test entropy computation - entropy = -p * log2(p)"""
        import math
        
        # Simple case: 2 words, equal probability letters at each position
        words = ['ab', 'cd']
        entropy_maps = compute_positional_letter_entropy(words)
        
        assert len(entropy_maps) == 2
        
        # Position 0: 'a' and 'c' each have p=0.5
        # Entropy = -0.5 * log2(0.5) = 0.5 * 1 = 0.5
        assert entropy_maps[0]['a'] == pytest.approx(-0.5 * math.log2(0.5))
        assert entropy_maps[0]['c'] == pytest.approx(-0.5 * math.log2(0.5))
        
        # Position 1: 'b' and 'd' each have p=0.5
        assert entropy_maps[1]['b'] == pytest.approx(0.5)
        assert entropy_maps[1]['d'] == pytest.approx(0.5)
    
    def test_compute_positional_letter_entropy_skewed(self):
        """Test entropy with skewed distribution - common letters have lower entropy"""
        import math
        
        # Position 0: 'a' appears 3 times, 'b' once
        words = ['ax', 'ay', 'az', 'bw']
        entropy_maps = compute_positional_letter_entropy(words)
        
        # 'a' has p=0.75, entropy = -0.75 * log2(0.75) ≈ 0.311
        # 'b' has p=0.25, entropy = -0.25 * log2(0.25) = 0.5
        assert entropy_maps[0]['a'] == pytest.approx(-0.75 * math.log2(0.75))
        assert entropy_maps[0]['b'] == pytest.approx(-0.25 * math.log2(0.25))
        
        # More common letter 'a' should have LOWER entropy than rare 'b'
        assert entropy_maps[0]['a'] < entropy_maps[0]['b']
    
    def test_compute_positional_letter_entropy_maximum(self):
        """Test that p=0.5 gives maximum entropy"""
        import math
        
        words = ['ab', 'cd', 'ef', 'gh']  # 4 words
        # Add skewed distribution: 'a' at pos 0 appears 3 times (p=0.75)
        words_skewed = ['ax', 'ay', 'az', 'bw']
        
        entropy_equal = compute_positional_letter_entropy(['ab', 'cd'])  # p=0.5 for all
        entropy_skewed = compute_positional_letter_entropy(words_skewed)  # p=0.75, 0.25
        
        # p=0.5 should have higher entropy than p=0.75
        max_entropy = -0.5 * math.log2(0.5)  # = 0.5
        assert entropy_equal[0]['a'] == pytest.approx(max_entropy)
        assert entropy_skewed[0]['a'] < max_entropy
    
    def test_compute_positional_letter_frequency_empty(self):
        """Test with empty word list"""
        words = []
        freq_maps = compute_positional_letter_frequency(words)
        
        assert freq_maps == []