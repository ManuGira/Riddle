import pytest
import numpy as np
import sys
from os.path import join as pjoin, dirname

# Add src directory to path
sys.path.insert(0, pjoin(dirname(__file__), "..", "src"))

from main_cluster import reduce_dimensions_pca


class TestReduceDimensionsPCA:
    """Tests for reduce_dimensions_pca function"""

    @pytest.fixture
    def sample_vectors(self):
        """Create sample vectors for testing"""
        # Create 100 samples with 50 features
        np.random.seed(42)
        return np.random.randn(100, 50)

    @pytest.fixture
    def low_rank_vectors(self):
        """Create low-rank vectors where most variance is in few dimensions"""
        np.random.seed(42)
        # Create data with most variance in first 3 dimensions
        base = np.random.randn(100, 3)
        noise = np.random.randn(100, 47) * 0.01  # Very small variance
        return np.hstack([base, noise])

    def test_reduce_dimensions_basic(self, sample_vectors):
        """Test basic PCA dimensionality reduction"""
        reduced_vectors, n_components = reduce_dimensions_pca(sample_vectors, variance_ratio=0.9)
        
        # Check return types
        assert isinstance(reduced_vectors, np.ndarray)
        assert isinstance(n_components, int)
        
        # Check that dimensions are reduced
        assert reduced_vectors.shape[0] == sample_vectors.shape[0]  # Same number of samples
        assert reduced_vectors.shape[1] < sample_vectors.shape[1]  # Fewer features
        assert reduced_vectors.shape[1] == n_components
        
    def test_variance_ratio_high(self, sample_vectors):
        """Test with high variance ratio (should keep more components)"""
        reduced_vectors, n_components = reduce_dimensions_pca(sample_vectors, variance_ratio=0.95)
        
        # Higher variance ratio should require more components
        assert n_components > 0
        assert n_components <= sample_vectors.shape[1]
        
    def test_variance_ratio_low(self, sample_vectors):
        """Test with low variance ratio (should keep fewer components)"""
        reduced_vectors, n_components = reduce_dimensions_pca(sample_vectors, variance_ratio=0.7)
        
        # Lower variance ratio should require fewer components
        assert n_components > 0
        assert n_components <= sample_vectors.shape[1]
        
    def test_variance_ratio_comparison(self, sample_vectors):
        """Test that higher variance ratio keeps more components"""
        _, n_components_low = reduce_dimensions_pca(sample_vectors, variance_ratio=0.7)
        _, n_components_high = reduce_dimensions_pca(sample_vectors, variance_ratio=0.95)
        
        assert n_components_high >= n_components_low
        
    def test_low_rank_data(self, low_rank_vectors):
        """Test with low-rank data (most variance in few dimensions)"""
        reduced_vectors, n_components = reduce_dimensions_pca(low_rank_vectors, variance_ratio=0.9)
        
        # Should identify that most variance is in few dimensions
        assert n_components <= 10  # Should be much less than 50
        
    def test_output_shape_consistency(self, sample_vectors):
        """Test that output shape is consistent with n_components"""
        reduced_vectors, n_components = reduce_dimensions_pca(sample_vectors, variance_ratio=0.9)
        
        assert reduced_vectors.shape == (sample_vectors.shape[0], n_components)
        
    def test_default_variance_ratio(self, sample_vectors):
        """Test that default variance ratio is 0.9"""
        reduced_vectors_default, n_components_default = reduce_dimensions_pca(sample_vectors)
        reduced_vectors_explicit, n_components_explicit = reduce_dimensions_pca(sample_vectors, variance_ratio=0.9)
        
        assert n_components_default == n_components_explicit
        assert np.allclose(reduced_vectors_default, reduced_vectors_explicit)
        
    def test_small_dataset(self):
        """Test with a very small dataset"""
        np.random.seed(42)
        small_vectors = np.random.randn(10, 5)
        
        reduced_vectors, n_components = reduce_dimensions_pca(small_vectors, variance_ratio=0.8)
        
        # Should work even with small data
        assert reduced_vectors.shape[0] == 10
        assert n_components <= 5
        
    def test_edge_case_high_variance(self, sample_vectors):
        """Test with variance ratio close to 1.0"""
        reduced_vectors, n_components = reduce_dimensions_pca(sample_vectors, variance_ratio=0.99)
        
        # Should keep most or all components
        assert n_components > 0
        assert n_components <= sample_vectors.shape[1]
        
    def test_edge_case_low_variance(self, sample_vectors):
        """Test with low variance ratio"""
        reduced_vectors, n_components = reduce_dimensions_pca(sample_vectors, variance_ratio=0.5)
        
        # Should keep at least 1 component
        assert n_components >= 1
        
    def test_input_not_modified(self, sample_vectors):
        """Test that input vectors are not modified"""
        original_vectors = sample_vectors.copy()
        
        reduce_dimensions_pca(sample_vectors, variance_ratio=0.9)
        
        # Original should remain unchanged
        assert np.allclose(sample_vectors, original_vectors)
        
    def test_reproducibility(self, sample_vectors):
        """Test that results are reproducible"""
        reduced_1, n_comp_1 = reduce_dimensions_pca(sample_vectors, variance_ratio=0.9)
        reduced_2, n_comp_2 = reduce_dimensions_pca(sample_vectors, variance_ratio=0.9)
        
        assert n_comp_1 == n_comp_2
        assert np.allclose(reduced_1, reduced_2)
