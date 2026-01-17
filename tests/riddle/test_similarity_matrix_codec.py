import numpy as np
import pytest
from pathlib import Path
import tempfile

from riddle.similarity_matrix_codec import (
    FullPrecisionMatrixCodec,
    LowPrecisionMatrixCodec,
    SparseMatrixCodec,
    save_similarity_matrix,
    load_similarity_matrix,
)


@pytest.fixture
def sample_similarity_matrix():
    """Create a sample similarity matrix for testing."""
    # Create a 5x5 symmetric similarity matrix with values in [-1, 1]
    matrix = np.array([
        [1.0, 0.8, 0.3, -0.2, 0.1],
        [0.8, 1.0, 0.5, 0.1, 0.2],
        [0.3, 0.5, 1.0, 0.6, 0.4],
        [-0.2, 0.1, 0.6, 1.0, 0.7],
        [0.1, 0.2, 0.4, 0.7, 1.0],
    ], dtype=np.float64)
    return matrix


@pytest.fixture
def sample_words():
    """Create sample words list."""
    return ["apple", "banana", "cherry", "date", "elderberry"]


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestFullPrecisionMatrixCodec:
    """Tests for FullPrecisionMatrixCodec."""
    
    def test_save_and_load(self, sample_similarity_matrix, sample_words, temp_dir):
        """Test saving and loading preserves the matrix exactly."""
        codec = FullPrecisionMatrixCodec()
        filepath = temp_dir / "test_full_precision.npz"
        
        # Save
        save_similarity_matrix(codec, sample_similarity_matrix, sample_words, filepath)
        
        # Verify file exists
        assert filepath.exists()
        
        # Load
        loaded_matrix, loaded_words = load_similarity_matrix(filepath, codec)
        
        # Verify exact match
        np.testing.assert_array_equal(loaded_matrix, sample_similarity_matrix)
        assert loaded_words == sample_words
    
    def test_load_with_universal_loader(self, sample_similarity_matrix, sample_words, temp_dir):
        """Test that universal loader works with full precision format."""
        codec = FullPrecisionMatrixCodec()
        filepath = temp_dir / "test_full_precision_universal.npz"
        
        save_similarity_matrix(codec, sample_similarity_matrix, sample_words, filepath)
        
        # Load with universal loader (no codec specified)
        loaded_matrix, loaded_words = load_similarity_matrix(filepath)
        
        np.testing.assert_array_equal(loaded_matrix, sample_similarity_matrix)
        assert loaded_words == sample_words
    
    def test_format_type_saved(self, sample_similarity_matrix, sample_words, temp_dir):
        """Test that format_type metadata is saved."""
        codec = FullPrecisionMatrixCodec()
        filepath = temp_dir / "test_format_type.npz"
        
        save_similarity_matrix(codec, sample_similarity_matrix, sample_words, filepath)
        
        # Check format_type
        data = np.load(filepath, allow_pickle=True)
        assert 'format_type' in data
        assert str(data['format_type']) == 'full_precision'


class TestLowPrecisionMatrixCodec:
    """Tests for LowPrecisionMatrixCodec."""
    
    def test_save_and_load(self, sample_similarity_matrix, sample_words, temp_dir):
        """Test saving and loading with uint8 precision."""
        codec = LowPrecisionMatrixCodec()
        filepath = temp_dir / "test_low_precision.npz"
        
        # Save
        save_similarity_matrix(codec, sample_similarity_matrix, sample_words, filepath)
        
        # Verify file exists
        assert filepath.exists()
        
        # Load
        loaded_matrix, loaded_words = load_similarity_matrix(filepath, codec)
        
        # Verify it's uint8
        assert loaded_matrix.dtype == np.uint8
        assert loaded_words == sample_words
        
        # Verify values are in correct range [0, 255]
        assert loaded_matrix.min() >= 0
        assert loaded_matrix.max() <= 255
    
    def test_precision_loss(self, sample_similarity_matrix, sample_words, temp_dir):
        """Test that conversion to uint8 causes expected precision loss."""
        codec = LowPrecisionMatrixCodec()
        filepath = temp_dir / "test_precision_loss.npz"
        
        save_similarity_matrix(codec, sample_similarity_matrix, sample_words, filepath)
        loaded_matrix, _ = load_similarity_matrix(filepath, codec)
        
        # Convert back to original range for comparison
        # Original encoding: ((matrix + 1) / 2 * 255)
        # So to decode: (matrix / 255) * 2 - 1
        decoded_matrix = (loaded_matrix.astype(np.float64) / 255.0) * 2 - 1
        
        # Should be approximately equal with tolerance for uint8 precision
        # Precision is roughly 2/255 ≈ 0.0078
        np.testing.assert_allclose(decoded_matrix, sample_similarity_matrix, atol=0.01)
    
    def test_load_with_universal_loader(self, sample_similarity_matrix, sample_words, temp_dir):
        """Test that universal loader works with low precision format."""
        codec = LowPrecisionMatrixCodec()
        filepath = temp_dir / "test_low_precision_universal.npz"
        
        save_similarity_matrix(codec, sample_similarity_matrix, sample_words, filepath)
        
        # Load with universal loader
        loaded_matrix, loaded_words = load_similarity_matrix(filepath)
        
        assert loaded_matrix.dtype == np.uint8
        assert loaded_words == sample_words
    
    def test_format_type_saved(self, sample_similarity_matrix, sample_words, temp_dir):
        """Test that format_type metadata is saved."""
        codec = LowPrecisionMatrixCodec()
        filepath = temp_dir / "test_format_type_low.npz"
        
        save_similarity_matrix(codec, sample_similarity_matrix, sample_words, filepath)
        
        # Check format_type
        data = np.load(filepath, allow_pickle=True)
        assert 'format_type' in data
        assert str(data['format_type']) == 'low_precision'


class TestSparseMatrixCodec:
    """Tests for SparseMatrixCodec."""
    
    def test_save_and_load_default_percentile(self, sample_similarity_matrix, sample_words, temp_dir):
        """Test saving and loading with default percentile."""
        codec = SparseMatrixCodec(percentile=95.0)
        filepath = temp_dir / "test_sparse.npz"
        
        # Save
        save_similarity_matrix(codec, sample_similarity_matrix, sample_words, filepath)
        
        # Verify file exists
        assert filepath.exists()
        
        # Load and reconstruct
        loaded_matrix, loaded_words = load_similarity_matrix(filepath, codec)
        
        # Verify shape and words
        assert loaded_matrix.shape == sample_similarity_matrix.shape
        assert loaded_words == sample_words
        
        # Verify diagonal is 1.0 (self-similarity)
        np.testing.assert_array_almost_equal(np.diag(loaded_matrix), np.ones(len(sample_words)))
        
        # Verify symmetry
        np.testing.assert_array_almost_equal(loaded_matrix, loaded_matrix.T)
    
    def test_different_percentiles(self, sample_similarity_matrix, sample_words, temp_dir):
        """Test that different percentiles produce different results."""
        codec_90 = SparseMatrixCodec(percentile=90.0)
        codec_95 = SparseMatrixCodec(percentile=95.0)
        
        filepath_90 = temp_dir / "test_sparse_90.npz"
        filepath_95 = temp_dir / "test_sparse_95.npz"
        
        save_similarity_matrix(codec_90, sample_similarity_matrix, sample_words, filepath_90)
        save_similarity_matrix(codec_95, sample_similarity_matrix, sample_words, filepath_95)
        
        # Load both
        loaded_90, _ = load_similarity_matrix(filepath_90, codec_90)
        loaded_95, _ = load_similarity_matrix(filepath_95, codec_95)
        
        # Both should be valid matrices
        assert loaded_90.shape == sample_similarity_matrix.shape
        assert loaded_95.shape == sample_similarity_matrix.shape
        
        # 90th percentile should preserve more non-zero values
        # Count non-zero off-diagonal elements
        non_diag_90 = np.count_nonzero(loaded_90 - np.diag(np.diag(loaded_90)))
        non_diag_95 = np.count_nonzero(loaded_95 - np.diag(np.diag(loaded_95)))
        
        assert non_diag_90 >= non_diag_95
    
    def test_high_similarity_values_preserved(self, sample_similarity_matrix, sample_words, temp_dir):
        """Test that high similarity values are preserved in sparse encoding."""
        codec = SparseMatrixCodec(percentile=70.0)  # Use lower percentile for small matrix
        filepath = temp_dir / "test_sparse_high_values.npz"
        
        save_similarity_matrix(codec, sample_similarity_matrix, sample_words, filepath)
        loaded_matrix, _ = load_similarity_matrix(filepath, codec)
        
        # The highest off-diagonal value should be preserved
        original_max = np.max(sample_similarity_matrix - np.diag(np.diag(sample_similarity_matrix)))
        loaded_max = np.max(loaded_matrix - np.diag(np.diag(loaded_matrix)))
        
        # Should be approximately equal (with some precision loss)
        assert abs(loaded_max - original_max) < 0.05
    
    def test_load_with_universal_loader(self, sample_similarity_matrix, sample_words, temp_dir):
        """Test that universal loader works with sparse format."""
        codec = SparseMatrixCodec(percentile=95.0)
        filepath = temp_dir / "test_sparse_universal.npz"
        
        save_similarity_matrix(codec, sample_similarity_matrix, sample_words, filepath)
        
        # Load with universal loader
        loaded_matrix, loaded_words = load_similarity_matrix(filepath)
        
        assert loaded_matrix.shape == sample_similarity_matrix.shape
        assert loaded_words == sample_words
    
    def test_format_type_saved(self, sample_similarity_matrix, sample_words, temp_dir):
        """Test that format_type metadata is saved."""
        codec = SparseMatrixCodec(percentile=95.0)
        filepath = temp_dir / "test_format_type_sparse.npz"
        
        save_similarity_matrix(codec, sample_similarity_matrix, sample_words, filepath)
        
        # Check format_type
        data = np.load(filepath, allow_pickle=True)
        assert 'format_type' in data
        assert str(data['format_type']) == 'sparse'
    
    def test_sparse_stores_vmin_vmax(self, sample_similarity_matrix, sample_words, temp_dir):
        """Test that vmin and vmax are stored in sparse format."""
        codec = SparseMatrixCodec(percentile=95.0)
        filepath = temp_dir / "test_sparse_metadata.npz"
        
        save_similarity_matrix(codec, sample_similarity_matrix, sample_words, filepath)
        
        # Check metadata
        data = np.load(filepath, allow_pickle=True)
        assert 'vmin' in data
        assert 'vmax' in data
        
        vmin = float(data['vmin'])
        vmax = float(data['vmax'])
        
        # vmin should be at 95th percentile
        expected_vmin = np.percentile(sample_similarity_matrix, 95.0)
        assert abs(vmin - expected_vmin) < 0.001
        
        # vmax should be the maximum value above vmin
        values_above_vmin = sample_similarity_matrix[sample_similarity_matrix >= expected_vmin]
        expected_vmax = values_above_vmin.max()
        assert abs(vmax - expected_vmax) < 0.001


class TestUniversalLoader:
    """Tests for the universal load_similarity_matrix function."""
    
    def test_invalid_format_type_raises_error(self, temp_dir):
        """Test that invalid format_type raises appropriate error."""
        filepath = temp_dir / "test_invalid.npz"
        
        # Create file with invalid format_type
        np.savez_compressed(filepath, matrix=np.array([1, 2, 3]), format_type='invalid_format')
        
        with pytest.raises(ValueError, match="Unknown format_type"):
            load_similarity_matrix(filepath)
    
    def test_missing_format_type_raises_error(self, temp_dir):
        """Test that missing format_type raises appropriate error."""
        filepath = temp_dir / "test_no_format.npz"
        
        # Create file without format_type
        np.savez_compressed(filepath, matrix=np.array([1, 2, 3]))
        
        with pytest.raises(ValueError, match="does not contain format_type metadata"):
            load_similarity_matrix(filepath)
    
    def test_loads_all_three_formats(self, sample_similarity_matrix, sample_words, temp_dir):
        """Test that universal loader can load all three formats."""
        codecs = [
            (FullPrecisionMatrixCodec(), "full.npz"),
            (LowPrecisionMatrixCodec(), "low.npz"),
            (SparseMatrixCodec(percentile=95.0), "sparse.npz"),
        ]
        
        for codec, filename in codecs:
            filepath = temp_dir / filename
            save_similarity_matrix(codec, sample_similarity_matrix, sample_words, filepath)
            
            # Should successfully load with universal loader
            loaded_matrix, loaded_words = load_similarity_matrix(filepath)
            
            assert loaded_matrix.shape == sample_similarity_matrix.shape
            assert loaded_words == sample_words


class TestEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_single_word_matrix(self, temp_dir):
        """Test with a 1x1 matrix (single word)."""
        matrix = np.array([[1.0]])
        words = ["word"]
        
        codec = FullPrecisionMatrixCodec()
        filepath = temp_dir / "test_single.npz"
        
        save_similarity_matrix(codec, matrix, words, filepath)
        loaded_matrix, loaded_words = load_similarity_matrix(filepath, codec)
        
        np.testing.assert_array_equal(loaded_matrix, matrix)
        assert loaded_words == words
    
    def test_empty_words_list(self, temp_dir):
        """Test with empty matrix and words list."""
        matrix = np.array([]).reshape(0, 0)
        words = []
        
        codec = FullPrecisionMatrixCodec()
        filepath = temp_dir / "test_empty.npz"
        
        save_similarity_matrix(codec, matrix, words, filepath)
        loaded_matrix, loaded_words = load_similarity_matrix(filepath, codec)
        
        assert loaded_matrix.shape == (0, 0)
        assert loaded_words == []
    
    def test_all_same_values_sparse(self, temp_dir):
        """Test sparse codec with matrix where all values are the same."""
        # All values are 0.5 except diagonal
        matrix = np.full((5, 5), 0.5, dtype=np.float64)
        np.fill_diagonal(matrix, 1.0)
        words = ["a", "b", "c", "d", "e"]
        
        codec = SparseMatrixCodec(percentile=95.0)
        filepath = temp_dir / "test_same_values.npz"
        
        save_similarity_matrix(codec, matrix, words, filepath)
        loaded_matrix, loaded_words = load_similarity_matrix(filepath, codec)
        
        # Should reconstruct something reasonable
        assert loaded_matrix.shape == matrix.shape
        assert loaded_words == words
        # Diagonal should still be 1.0
        np.testing.assert_array_almost_equal(np.diag(loaded_matrix), np.ones(5))
