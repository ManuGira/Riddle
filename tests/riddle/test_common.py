import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from riddle.common import (compute_correlation_matrix, compute_distance_matrix,
                           compute_heatmap_matrix, compute_similarity_matrix,
                           load_most_frequent_words)


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
