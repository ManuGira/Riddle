import pytest
import numpy as np
import sys
from os.path import join as pjoin, dirname

# Add src directory to path
sys.path.insert(0, pjoin(dirname(__file__), "..", "src"))

from main_cluster import reduce_dimensions_pca, cluster_with_knn, suggest_eps_values, cluster_with_kmeans


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
    def sample_vectors(self):
        """Create sample vectors for testing"""
        np.random.seed(42)
        # Create 50 samples with 10 features
        return np.random.randn(50, 10)

    @pytest.fixture
    def clustered_vectors(self):
        """Create vectors that naturally form clusters"""
        np.random.seed(42)
        # Create 3 distinct clusters
        cluster1 = np.random.randn(20, 10) + np.array([10, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        cluster2 = np.random.randn(20, 10) + np.array([0, 10, 0, 0, 0, 0, 0, 0, 0, 0])
        cluster3 = np.random.randn(20, 10) + np.array([0, 0, 10, 0, 0, 0, 0, 0, 0, 0])
        return np.vstack([cluster1, cluster2, cluster3])

    def test_cluster_basic(self, sample_vectors):
        """Test basic DBSCAN clustering with eps"""
        eps = 0.5
        cluster_labels = cluster_with_knn(sample_vectors, eps=eps)
        
        # Check return type
        assert isinstance(cluster_labels, np.ndarray)
        
        # Check output shape matches input
        assert cluster_labels.shape[0] == sample_vectors.shape[0]
        
        # Check that labels are integers
        assert np.issubdtype(cluster_labels.dtype, np.integer)
        
        # Check that we have at least one cluster
        assert len(np.unique(cluster_labels)) >= 1

    def test_cluster_count_reasonable(self, sample_vectors):
        """Test that number of clusters is reasonable"""
        eps = 0.5
        cluster_labels = cluster_with_knn(sample_vectors, eps=eps)
        
        n_clusters = len(np.unique(cluster_labels))
        
        # Should have fewer clusters than samples
        assert n_clusters < sample_vectors.shape[0]
        # Should have at least 1 cluster
        assert n_clusters >= 1

    def test_different_eps_values(self, sample_vectors):
        """Test with different eps values"""
        labels_small = cluster_with_knn(sample_vectors, eps=0.3)
        labels_large = cluster_with_knn(sample_vectors, eps=0.7)
        
        # Both should produce valid results
        assert labels_small.shape[0] == sample_vectors.shape[0]
        assert labels_large.shape[0] == sample_vectors.shape[0]
        
        # Different eps values may produce different clusterings
        assert len(np.unique(labels_small)) >= 1
        assert len(np.unique(labels_large)) >= 1

    def test_min_samples_parameter(self, sample_vectors):
        """Test with different min_samples values"""
        eps = 0.5
        labels_min2 = cluster_with_knn(sample_vectors, eps=eps, min_samples=2)
        labels_min5 = cluster_with_knn(sample_vectors, eps=eps, min_samples=5)
        
        # Both should produce valid results
        assert labels_min2.shape[0] == sample_vectors.shape[0]
        assert labels_min5.shape[0] == sample_vectors.shape[0]

    def test_distinct_clusters(self, clustered_vectors):
        """Test with well-separated clusters"""
        # Use a small eps to find distinct clusters
        eps = 0.5
        cluster_labels = cluster_with_knn(clustered_vectors, eps=eps)
        
        # Should find at least one cluster
        n_clusters = len(np.unique(cluster_labels))
        assert n_clusters >= 1
        
        # Each cluster should have some points
        for label in np.unique(cluster_labels):
            assert np.sum(cluster_labels == label) > 0

    def test_small_dataset(self):
        """Test with a very small dataset"""
        np.random.seed(42)
        small_vectors = np.random.randn(10, 5)
        
        eps = 0.5
        cluster_labels = cluster_with_knn(small_vectors, eps=eps, min_samples=2)
        
        # Should handle small datasets
        assert cluster_labels.shape[0] == 10
        assert len(np.unique(cluster_labels)) >= 1

    def test_reproducibility(self, sample_vectors):
        """Test that results are reproducible"""
        eps = 0.5
        labels_1 = cluster_with_knn(sample_vectors, eps=eps)
        labels_2 = cluster_with_knn(sample_vectors, eps=eps)
        
        assert np.array_equal(labels_1, labels_2)

    def test_input_not_modified(self, sample_vectors):
        """Test that input vectors are not modified"""
        original_vectors = sample_vectors.copy()
        eps = 0.5
        
        cluster_with_knn(sample_vectors, eps=eps)
        
        # Original should remain unchanged
        assert np.allclose(sample_vectors, original_vectors)

    def test_2d_vectors(self):
        """Test with 2D vectors (already reduced)"""
        np.random.seed(42)
        vectors_2d = np.random.randn(30, 2)
        
        eps = 0.5
        cluster_labels = cluster_with_knn(vectors_2d, eps=eps)
        
        assert cluster_labels.shape[0] == 30
        assert len(np.unique(cluster_labels)) >= 1

    def test_high_dimensional_vectors(self):
        """Test with high-dimensional vectors"""
        np.random.seed(42)
        high_dim_vectors = np.random.randn(100, 100)
        
        eps = 0.5
        cluster_labels = cluster_with_knn(high_dim_vectors, eps=eps)
        
        assert cluster_labels.shape[0] == 100
        assert len(np.unique(cluster_labels)) >= 1


class TestSuggestEpsValues:
    """Tests for suggest_eps_values function"""

    @pytest.fixture
    def sample_vectors(self):
        """Create sample vectors for testing"""
        np.random.seed(42)
        return np.random.randn(50, 10)

    def test_suggest_eps_basic(self, sample_vectors):
        """Test basic eps suggestion"""
        eps_values = suggest_eps_values(sample_vectors, k=5)
        
        # Check return type
        assert isinstance(eps_values, dict)
        
        # Check all expected keys are present
        expected_keys = ['min', 'percentile_25', 'median', 'percentile_75', 'max']
        assert all(key in eps_values for key in expected_keys)
        
        # Check that values are floats
        assert all(isinstance(v, float) for v in eps_values.values())
        
        # Check that values are in ascending order
        assert eps_values['min'] <= eps_values['percentile_25']
        assert eps_values['percentile_25'] <= eps_values['median']
        assert eps_values['median'] <= eps_values['percentile_75']
        assert eps_values['percentile_75'] <= eps_values['max']

    def test_suggest_eps_different_k(self, sample_vectors):
        """Test with different k values"""
        eps_k3 = suggest_eps_values(sample_vectors, k=3)
        eps_k7 = suggest_eps_values(sample_vectors, k=7)
        
        # Both should return valid dictionaries
        assert isinstance(eps_k3, dict)
        assert isinstance(eps_k7, dict)
        
        # k=7 should generally have larger distances than k=3
        # (because 7th neighbor is farther than 3rd neighbor)
        assert eps_k7['median'] >= eps_k3['median']

    def test_suggest_eps_small_dataset(self):
        """Test with small dataset"""
        np.random.seed(42)
        small_vectors = np.random.randn(5, 3)
        
        eps_values = suggest_eps_values(small_vectors, k=10)
        
        # Should still return valid values
        assert isinstance(eps_values, dict)
        assert all(isinstance(v, float) for v in eps_values.values())

class TestClusterWithKMeans:
    """Tests for cluster_with_kmeans function"""

    @pytest.fixture
    def sample_vectors(self):
        """Create sample vectors for testing"""
        np.random.seed(42)
        # Create 50 samples with 10 features
        return np.random.randn(50, 10)

    @pytest.fixture
    def clustered_vectors(self):
        """Create vectors that naturally form clusters"""
        np.random.seed(42)
        # Create 3 distinct clusters
        cluster1 = np.random.randn(20, 10) + np.array([10, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        cluster2 = np.random.randn(20, 10) + np.array([0, 10, 0, 0, 0, 0, 0, 0, 0, 0])
        cluster3 = np.random.randn(20, 10) + np.array([0, 0, 10, 0, 0, 0, 0, 0, 0, 0])
        return np.vstack([cluster1, cluster2, cluster3])

    def test_kmeans_basic(self, sample_vectors):
        """Test basic k-means clustering"""
        n_clusters = 3
        cluster_labels, _, _ = cluster_with_kmeans(sample_vectors, n_clusters=n_clusters)
        
        # Check return type
        assert isinstance(cluster_labels, np.ndarray)
        
        # Check output shape matches input
        assert cluster_labels.shape[0] == sample_vectors.shape[0]
        
        # Check that labels are integers
        assert np.issubdtype(cluster_labels.dtype, np.integer)
        
        # Check that we have the requested number of clusters
        assert len(np.unique(cluster_labels)) == n_clusters

    def test_kmeans_different_n_clusters(self, sample_vectors):
        """Test with different numbers of clusters"""
        cluster_labels_2, _, _ = cluster_with_kmeans(sample_vectors, n_clusters=2)
        cluster_labels_5, _, _ = cluster_with_kmeans(sample_vectors, n_clusters=5)
        
        # Both should produce valid results
        assert cluster_labels_2.shape[0] == sample_vectors.shape[0]
        assert cluster_labels_5.shape[0] == sample_vectors.shape[0]
        
        # Should have the requested number of clusters
        assert len(np.unique(cluster_labels_2)) == 2
        assert len(np.unique(cluster_labels_5)) == 5
    def test_kmeans_distinct_clusters(self, clustered_vectors):
        """Test with well-separated clusters"""
        cluster_labels, _, _ = cluster_with_kmeans(clustered_vectors, n_clusters=3)
        
        # Should find exactly 3 clusters
        n_clusters = len(np.unique(cluster_labels))
        assert n_clusters == 3
        
        # Each cluster should have some points
        for label in np.unique(cluster_labels):
            assert np.sum(cluster_labels == label) > 0

    def test_kmeans_single_cluster(self, sample_vectors):
        """Test with single cluster"""
        cluster_labels, _, _ = cluster_with_kmeans(sample_vectors, n_clusters=1)
        
        # All points should be in the same cluster
        assert len(np.unique(cluster_labels)) == 1
        assert np.all(cluster_labels == 0)

    def test_kmeans_small_dataset(self):
        """Test with a very small dataset"""
        np.random.seed(42)
        small_vectors = np.random.randn(10, 5)
        
        cluster_labels, _, _ = cluster_with_kmeans(small_vectors, n_clusters=3)
        
        # Should handle small datasets
        assert cluster_labels.shape[0] == 10
        assert len(np.unique(cluster_labels)) == 3

    def test_kmeans_reproducibility(self, sample_vectors):
        """Test that results are reproducible with same random_state"""
        cluster_labels_1, _, _  = cluster_with_kmeans(sample_vectors, n_clusters=3, random_state=42)
        cluster_labels_2, _, _  = cluster_with_kmeans(sample_vectors, n_clusters=3, random_state=42)
        
        assert np.array_equal(cluster_labels_1, cluster_labels_2)

    def test_kmeans_input_not_modified(self, sample_vectors):
        """Test that input vectors are not modified"""
        original_vectors = sample_vectors.copy()
        
        cluster_with_kmeans(sample_vectors, n_clusters=3)
        
        # Original should remain unchanged
        assert np.allclose(sample_vectors, original_vectors)

    def test_kmeans_2d_vectors(self):
        """Test with 2D vectors"""
        np.random.seed(42)
        vectors_2d = np.random.randn(30, 2)
        
        cluster_labels, _, _ = cluster_with_kmeans(vectors_2d, n_clusters=4)
       
        
        assert cluster_labels.shape[0] == 30
        assert len(np.unique(cluster_labels)) == 4

    def test_kmeans_high_dimensional_vectors(self):
        """Test with high-dimensional vectors"""
        np.random.seed(42)
        high_dim_vectors = np.random.randn(100, 100)
        
        result = cluster_with_kmeans(high_dim_vectors, n_clusters=5)
        cluster_labels, _, _ = result
        
        assert cluster_labels.shape[0] == 100
        assert len(np.unique(cluster_labels)) == 5
