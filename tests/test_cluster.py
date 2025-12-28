import pytest
import numpy as np
import sys
from os.path import join as pjoin, dirname

# Add src directory to path
sys.path.insert(0, pjoin(dirname(__file__), "..", "src"))

from main_cluster import reduce_dimensions_pca, cluster_with_knn


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


class TestClusterWithKNN:
    """Tests for cluster_with_knn function"""

    @pytest.fixture
    def simple_clustered_data(self):
        """Create simple data with obvious clusters"""
        np.random.seed(42)
        # Create 3 distinct clusters
        cluster1 = np.random.randn(20, 2) + np.array([0, 0])
        cluster2 = np.random.randn(20, 2) + np.array([10, 10])
        cluster3 = np.random.randn(20, 2) + np.array([10, -10])
        return np.vstack([cluster1, cluster2, cluster3])

    @pytest.fixture
    def linear_data(self):
        """Create linearly arranged data"""
        np.random.seed(42)
        # Points arranged in a line
        x = np.linspace(0, 10, 50)
        y = x + np.random.randn(50) * 0.1
        return np.column_stack([x, y])

    @pytest.fixture
    def sample_vectors(self):
        """Create sample vectors for testing"""
        np.random.seed(42)
        return np.random.randn(50, 10)

    def test_cluster_basic_functionality(self, simple_clustered_data):
        """Test basic clustering functionality"""
        cluster_labels = cluster_with_knn(simple_clustered_data, k=5)
        
        # Check return type
        assert isinstance(cluster_labels, np.ndarray)
        
        # Check shape matches input
        assert cluster_labels.shape[0] == simple_clustered_data.shape[0]
        
        # Check that we have at least one cluster
        n_clusters = len(np.unique(cluster_labels))
        assert n_clusters >= 1
        
    def test_cluster_labels_are_integers(self, sample_vectors):
        """Test that cluster labels are integers"""
        cluster_labels = cluster_with_knn(sample_vectors, k=5)
        
        # All labels should be integers
        assert np.issubdtype(cluster_labels.dtype, np.integer)
        
    def test_cluster_labels_start_from_zero(self, sample_vectors):
        """Test that cluster labels start from 0"""
        cluster_labels = cluster_with_knn(sample_vectors, k=5)
        
        # Labels should start from 0
        assert np.min(cluster_labels) == 0
        
    def test_cluster_labels_are_consecutive(self, sample_vectors):
        """Test that cluster labels are consecutive (0, 1, 2, ...)"""
        cluster_labels = cluster_with_knn(sample_vectors, k=5)
        
        unique_labels = np.unique(cluster_labels)
        # Labels should be consecutive starting from 0
        expected_labels = np.arange(len(unique_labels))
        assert np.array_equal(unique_labels, expected_labels)
        
    def test_different_k_values(self, simple_clustered_data):
        """Test with different k values"""
        labels_k3 = cluster_with_knn(simple_clustered_data, k=3)
        labels_k7 = cluster_with_knn(simple_clustered_data, k=7)
        
        # Both should produce valid results
        assert labels_k3.shape[0] == simple_clustered_data.shape[0]
        assert labels_k7.shape[0] == simple_clustered_data.shape[0]
        
        # Both should have at least one cluster
        assert len(np.unique(labels_k3)) >= 1
        assert len(np.unique(labels_k7)) >= 1
        
    def test_default_k_value(self, sample_vectors):
        """Test that default k value is 5"""
        labels_default = cluster_with_knn(sample_vectors)
        labels_explicit = cluster_with_knn(sample_vectors, k=5)
        
        assert np.array_equal(labels_default, labels_explicit)
        
    def test_small_dataset(self):
        """Test with a very small dataset"""
        np.random.seed(42)
        small_vectors = np.random.randn(10, 3)
        
        cluster_labels = cluster_with_knn(small_vectors, k=3)
        
        # Should work even with small data
        assert cluster_labels.shape[0] == 10
        assert len(np.unique(cluster_labels)) >= 1
        
    def test_high_dimensional_data(self):
        """Test with high-dimensional data"""
        np.random.seed(42)
        high_dim_vectors = np.random.randn(30, 100)
        
        cluster_labels = cluster_with_knn(high_dim_vectors, k=5)
        
        # Should handle high dimensions
        assert cluster_labels.shape[0] == 30
        assert len(np.unique(cluster_labels)) >= 1
        
    def test_input_not_modified(self, sample_vectors):
        """Test that input vectors are not modified"""
        original_vectors = sample_vectors.copy()
        
        cluster_with_knn(sample_vectors, k=5)
        
        # Original should remain unchanged
        assert np.allclose(sample_vectors, original_vectors)
        
    def test_reproducibility(self, sample_vectors):
        """Test that results are reproducible"""
        labels_1 = cluster_with_knn(sample_vectors, k=5)
        labels_2 = cluster_with_knn(sample_vectors, k=5)
        
        assert np.array_equal(labels_1, labels_2)
        
    def test_well_separated_clusters(self, simple_clustered_data):
        """Test that well-separated clusters are detected"""
        cluster_labels = cluster_with_knn(simple_clustered_data, k=5)
        
        # With 3 well-separated clusters, we should get reasonable clustering
        n_clusters = len(np.unique(cluster_labels))
        # Should detect at least 2 clusters (being conservative)
        assert n_clusters >= 2
        
    def test_k_larger_than_dataset(self):
        """Test edge case where k is larger than dataset size"""
        np.random.seed(42)
        tiny_vectors = np.random.randn(5, 3)
        
        # k=10 is larger than dataset size (5)
        # Should still work (algorithm should handle this gracefully)
        cluster_labels = cluster_with_knn(tiny_vectors, k=10)
        
        assert cluster_labels.shape[0] == 5
        assert len(np.unique(cluster_labels)) >= 1
