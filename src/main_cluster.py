"""
Word clustering module using DBSCAN and K-Means with cosine distance.

This module provides two clustering approaches:
1. DBSCAN: Density-based clustering (no need to specify number of clusters)
2. K-Means: Centroid-based clustering (requires specifying number of clusters)

Usage examples:

    # DBSCAN clustering
    suggested_eps = suggest_eps_values(vectors, k=5)
    cluster_labels = cluster_with_knn(vectors, eps=suggested_eps['median'], min_samples=2)
    
    # K-Means clustering
    cluster_labels = cluster_with_kmeans(vectors, n_clusters=5)
"""
import logging
import time

import numpy as np

import common as cmn

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def extract_word_vectors(model, words: list[str]) -> np.ndarray:
    """
    Extract word vectors for the given words from the model.
    
    Args:
        model: Word2vec model
        words: list of words to extract vectors for
        
    Returns:
        tuple of (valid_words, vectors) where valid_words are words that exist in the model
        and vectors is a numpy array of shape (n_words, vector_dim)
    """
    indexes = [model.key_to_index[word] for word in words]
    vectors = np.array([model.vectors[index] for index in indexes])
    return vectors

def reduce_dimensions_pca(vectors: np.ndarray, variance_ratio: float = 0.9) -> tuple[np.ndarray, int]:
    """
    Reduce dimensionality using PCA while preserving specified variance.
    
    Args:
        vectors: Input vectors of shape (n_samples, n_features)
        variance_ratio: Amount of variance to preserve (0.0 to 1.0)
        
    Returns:
        tuple of (reduced_vectors, n_components) where reduced_vectors are the transformed
        vectors and n_components is the number of dimensions kept
    """
    from sklearn.decomposition import PCA

    # Fit PCA with all components to get variance ratios
    pca = PCA()
    pca.fit(vectors)
    
    # Find how many components are needed to preserve the variance ratio
    cumsum_variance = np.cumsum(pca.explained_variance_ratio_)
    n_components = int(np.argmax(cumsum_variance >= variance_ratio) + 1)

    # Refit with the determined number of components
    pca = PCA(n_components=n_components)
    reduced_vectors = pca.fit_transform(vectors)
    
    return reduced_vectors, n_components


def suggest_eps_values(vectors: np.ndarray, k: int = 5) -> dict[str, float]:
    """
    Suggest good eps values for DBSCAN clustering based on kNN distances.
    
    Args:
        vectors: Word vectors of shape (n_words, n_features)
        k: Number of nearest neighbors to consider
        
    Returns:
        Dictionary with suggested eps values (min, percentile_25, median, percentile_75, max)
    """
    from sklearn.neighbors import NearestNeighbors
    
    n_samples = vectors.shape[0]
    k_adjusted = min(k, n_samples - 1)
    
    if k_adjusted > 0:
        nbrs = NearestNeighbors(n_neighbors=k_adjusted + 1, algorithm='auto', metric='cosine')
        nbrs.fit(vectors)
        distances, indices = nbrs.kneighbors(vectors)
        
        # Take the distance to the kth nearest neighbor (excluding self)
        kth_distances = distances[:, -1]
        
        return {
            'min': float(np.min(kth_distances)),
            'percentile_25': float(np.percentile(kth_distances, 25)),
            'median': float(np.median(kth_distances)),
            'percentile_75': float(np.percentile(kth_distances, 75)),
            'max': float(np.max(kth_distances)),
        }
    else:
        return {
            'min': 0.1,
            'percentile_25': 0.25,
            'median': 0.5,
            'percentile_75': 0.75,
            'max': 1.0,
        }


def cluster_with_knn(vectors: np.ndarray, eps: float, min_samples: int = 2) -> np.ndarray:
    """
    Cluster words using DBSCAN with cosine distance.
    
    Args:
        vectors: Word vectors of shape (n_words, n_features)
        eps: Maximum distance between two samples for them to be in the same neighborhood
        min_samples: Minimum number of samples in a neighborhood for a core point
        
    Returns:
        Cluster assignments for each word
    """
    from sklearn.cluster import DBSCAN
    
    # Apply DBSCAN clustering with cosine distance
    dbscan = DBSCAN(eps=eps, min_samples=min_samples, metric='cosine')
    cluster_labels = dbscan.fit_predict(vectors)
    
    # DBSCAN returns -1 for noise points; convert to positive labels
    if np.any(cluster_labels == -1):
        # Shift all labels to be non-negative
        cluster_labels = cluster_labels + 1
    
    return cluster_labels


def cluster_with_kmeans(vectors: np.ndarray, n_clusters: int, random_state: int = None) -> np.ndarray:
    """
    Cluster words using k-means with cosine or euclidean distance.
    
    Args:
        vectors: Word vectors of shape (n_words, n_features)
        n_clusters: Number of clusters to form
        random_state: Random state for reproducibility
        
    Returns:
        Cluster assignments for each word
    """
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import normalize

    # For cosine distance, normalize vectors first
    # Then use euclidean distance on normalized vectors
    # This is equivalent to cosine similarity
    normalized_vectors = normalize(vectors, norm='l2')
    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    cluster_labels = kmeans.fit_predict(normalized_vectors)

    # get fit error
    inertia = kmeans.inertia_

    # get centroids
    centroids = kmeans.cluster_centers_

    return cluster_labels, centroids, inertia


def compute_clusters_with_knn(vectors, words, k):
    # Step 5: Get suggested eps values
    logger.info(f"Computing suggested eps values (k={k})...")
    suggested_eps = suggest_eps_values(vectors, k=k)
    logger.info(f"Suggested eps values: {suggested_eps}")
    # Step 6: Try clustering with multiple eps values
    eps_values_to_try = [
        suggested_eps['min'],
        suggested_eps['percentile_25'],
        suggested_eps['median'],
        suggested_eps['percentile_75'],
        suggested_eps['max'],
    ]
    # Also try some smaller manual values if suggested values are large
    if suggested_eps['median'] > 1.0:
        logger.info("Suggested eps values are large. Adding smaller values to try...")
        eps_values_to_try = [0.5, 0.7, 0.9] + eps_values_to_try
    for eps in eps_values_to_try:
        logger.info(f"Clustering with eps={eps:.4f}...")
        tick = time.time()
        cluster_labels = cluster_with_knn(vectors, eps=eps, min_samples=2)
        n_clusters = len(np.unique(cluster_labels))
        tock = time.time()
        logger.info(f"  Found {n_clusters} clusters in {tock - tick:.2f} seconds")
        plot_word_space(words, vectors, cluster_labels)
    # Use median eps for final results
    eps_final = suggested_eps['median']
    logger.info(f"Using eps={eps_final:.4f} for final clustering...")
    cluster_labels = cluster_with_knn(vectors, eps=eps_final, min_samples=2)
    n_clusters = len(np.unique(cluster_labels))
    logger.info(f"Final clustering: {n_clusters} clusters")
    return cluster_labels


def compute_clusters_with_kmeans(vectors):
    """
    Try k-means clustering with different numbers of clusters.
    
    Args:
        vectors: Reduced word vectors
        words: List of words
        n_clusters_range: List of cluster counts to try (default: [2, 3, 4, 5])
    
    Returns:
        Cluster labels using the median number of clusters
    """

    logger.info(f"Trying K-Means clustering with different cluster counts...")

    inertias = []
    n_clusters_range = [2**i for i in range(1, 10)]
    for n_clusters in n_clusters_range:
        logger.info(f"K-Means with n_clusters={n_clusters}...")
        tick = time.time()
        cluster_labels, centroids, inertia = cluster_with_kmeans(vectors, n_clusters=n_clusters, random_state=42)
        tock = time.time()
        logger.info(f"  Completed in {tock - tick:.2f} seconds")
        inertias.append(inertia)

        # plot_word_space(words, vectors, cluster_labels)

    import matplotlib.pyplot as plt
    plt.plot(n_clusters_range, inertias)
    plt.grid()
    plt.show()

    # Use median number of clusters for final results
    n_clusters_final = n_clusters_range[len(n_clusters_range) // 2]
    logger.info(f"Using n_clusters={n_clusters_final} for final K-Means clustering...")
    cluster_labels = cluster_with_kmeans(vectors, n_clusters=n_clusters_final, random_state=42)
    logger.info(f"Final K-Means clustering: {n_clusters_final} clusters")
    return cluster_labels


def plot_word_space(words, vectors, cluster_labels=None):
    # Plot 2D scatter plot with clusters
    import matplotlib.pyplot as plt
    plt.figure(figsize=(8, 6))
    if cluster_labels is None:
        scatter = plt.scatter(vectors[:, 0], vectors[:, 1])
    else:
        scatter = plt.scatter(vectors[:, 0], vectors[:, 1], c=cluster_labels, cmap='tab10')

    for i, word in enumerate(words):
        plt.annotate(word, (vectors[i, 0], vectors[i, 1]))
    plt.title("Word Clusters in 2D PCA Space")
    plt.xlabel("PCA Component 1")
    plt.ylabel("PCA Component 2")
    plt.grid()

    if cluster_labels is not None:
        plt.legend(*scatter.legend_elements(), title="Clusters")

    plt.show()


def save_clusters(words: list[str], cluster_labels: np.ndarray, output_file: str):
    """
    Save word clusters to a file.
    
    Args:
        words: list of words
        cluster_labels: Cluster assignment for each word
        output_file: Path to output file
    """
    # TODO: Implement cluster saving
    raise NotImplementedError


def visualize_clusters(words: list[str], vectors: np.ndarray, cluster_labels: np.ndarray):
    """
    Visualize word clusters in 2D space.
    
    Args:
        words: list of words
        vectors: Word vectors (will be reduced to 2D if needed)
        cluster_labels: Cluster assignment for each word
    """
    # TODO: Implement cluster visualization
    raise NotImplementedError

def distance_to_centroid(word_vectors: np.ndarray, centroid_vectors: np.ndarray) -> float:
    # l2 norm on horizontal axis
    pass


def main():
    """
    Load word2vec model,
    Load frequent words,
    Extract vector list for those words,
    Compute PCA to reduce dimensions, keeping 90% variance,
    Cluster the words based on reduced vectors with kNN,
    """
    logger.info("Starting word clustering pipeline...")
    
    # Configuration
    MODEL_PATH = "frWac_non_lem_no_postag_no_phrase_200_cbow_cut100.bin"  # TODO: Update with actual path
    FREQUENCY_FILE = "data/frequency.txt"
    TOP_N_WORDS = 1000
    VARIANCE_RATIO = 0.9
    K_NEIGHBORS = 10
    OUTPUT_FILE = "data/word_clusters.txt"
    
    # Step 1: Load word2vec model
    logger.info("Loading word2vec model...")
    model = cmn.load_model(MODEL_PATH)

    # Step 2: Load frequent words
    logger.info(f"Loading top {TOP_N_WORDS} frequent words...")
    frequent_words = cmn.load_most_frequent_words(TOP_N_WORDS, model)
    # frequent_words = load_frequent_words(FREQUENCY_FILE, top_n=TOP_N_WORDS)
    # frequent_words = ["roi", "reine", "banane", "pomme", "voiture", "camion", "avion", "bateau", "félin", "chat", "chien"]
    
    # Step 3: Extract vectors for those words
    logger.info("Extracting word vectors...")
    word_vectors = extract_word_vectors(model, frequent_words)
    initial_dimensionality = word_vectors.shape[1]
    logger.info(f"Extracted vectors with dimension {initial_dimensionality}")
    
    # Step 4: Compute PCA to reduce dimensions
    logger.info(f"Reducing dimensions with PCA (preserving {VARIANCE_RATIO*100}% variance)...")
    tick = time.time()
    reduced_vectors, n_components = reduce_dimensions_pca(word_vectors, variance_ratio=VARIANCE_RATIO)
    tock = time.time()
    logger.info(f"PCA completed in {tock - tick:.2f} seconds. Reduced from {initial_dimensionality} to {n_components} dimensions")

    # plot_word_space(frequent_words, reduced_vectors)

    # # Try both clustering methods
    # logger.info("\n" + "="*60)
    # logger.info("Method 1: DBSCAN Clustering (density-based)")
    # logger.info("="*60)
    # cluster_labels = compute_clusters_with_knn(reduced_vectors, frequent_words, K_NEIGHBORS)

    logger.info("\n" + "="*60)
    logger.info("Method 2: K-Means Clustering (centroid-based)")
    logger.info("="*60)
    # cluster_labels = compute_clusters_with_kmeans(reduced_vectors)
    cluster_labels, centroids, inertia = cluster_with_kmeans(reduced_vectors, n_clusters=10, random_state=42)

    for label in np.unique(cluster_labels):
        cluster_words = [frequent_words[i] for i in range(len(frequent_words)) if cluster_labels[i] == label]
        # find the word of the cluster the furthest from other clusters

        logger.info(f"Cluster {label}: {cluster_words}")

    # Step 7: Save results
    logger.info("\nSaving clusters...")
    # save_clusters(frequent_words, cluster_labels_dbscan, OUTPUT_FILE)
    
    # Step 8: Visualize clusters
    logger.info("Visualizing clusters...")
    # visualize_clusters(frequent_words, reduced_vectors, cluster_labels)
    
    logger.info("Clustering pipeline completed successfully!")




if __name__ == "__main__":
    main()



