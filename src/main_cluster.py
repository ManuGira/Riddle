import logging
import time

import numpy as np

import common as cmn

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_frequent_words(frequency_file: str, top_n: int = 1000) -> list[str]:
    """
    Load the most frequent words from a frequency file.

    Args:
        frequency_file: Path to the frequency file
        top_n: Number of top frequent words to load
    Returns:
        List of frequent words
    """


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


def cluster_with_knn(vectors: np.ndarray, k: int = 5) -> np.ndarray:
    """
    Cluster words using k-nearest neighbors approach.
    
    Args:
        vectors: Word vectors of shape (n_words, n_features)
        k: Number of nearest neighbors to consider
        
    Returns:
        Cluster assignments for each word
    """
    from sklearn.neighbors import NearestNeighbors
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import connected_components
    
    n_samples = vectors.shape[0]
    
    # Handle edge case where k is larger than dataset size
    k_effective = min(k, n_samples - 1)
    
    # Build k-nearest neighbors graph
    nbrs = NearestNeighbors(n_neighbors=k_effective + 1, algorithm='auto').fit(vectors)
    distances, indices = nbrs.kneighbors(vectors)
    
    # Build adjacency matrix (symmetric graph)
    # Create edges between each point and its k-nearest neighbors
    row_indices = np.repeat(np.arange(n_samples), k_effective + 1)
    col_indices = indices.flatten()
    data = np.ones(len(row_indices))
    
    # Create sparse adjacency matrix
    adjacency_matrix = csr_matrix((data, (row_indices, col_indices)), 
                                   shape=(n_samples, n_samples))
    
    # Make the graph symmetric
    adjacency_matrix = adjacency_matrix + adjacency_matrix.T
    
    # Find connected components (clusters)
    n_components, labels = connected_components(csgraph=adjacency_matrix, 
                                                 directed=False, 
                                                 return_labels=True)
    
    return labels


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
    K_NEIGHBORS = 5
    OUTPUT_FILE = "data/word_clusters.txt"
    
    # Step 1: Load word2vec model
    logger.info("Loading word2vec model...")
    model = cmn.load_model(MODEL_PATH)

    # Step 2: Load frequent words
    logger.info(f"Loading top {TOP_N_WORDS} frequent words...")
    # frequent_words = cmn.load_most_frequent_words(TOP_N_WORDS, model)
    # frequent_words = load_frequent_words(FREQUENCY_FILE, top_n=TOP_N_WORDS)
    frequent_words = ["roi", "reine", "banane", "pomme", "voiture", "camion", "avion", "bateau", "félin", "chat", "chien"]
    
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
    logger.info(f"PCA completed in {tock - tick:.2f} seconds, reduced from {initial_dimensionality} to {n_components} dimensions")
    
    # Step 5: Cluster words using kNN
    logger.info(f"Clustering words with kNN (k={K_NEIGHBORS})...")
    cluster_labels = cluster_with_knn(reduced_vectors, k=K_NEIGHBORS)
    n_clusters = len(np.unique(cluster_labels))
    logger.info(f"Found {n_clusters} clusters")
    
    # Step 6: Save results
    logger.info("Saving clusters...")
    save_clusters(valid_words, cluster_labels, OUTPUT_FILE)
    
    # Step 7: Visualize clusters
    logger.info("Visualizing clusters...")
    visualize_clusters(valid_words, reduced_vectors, cluster_labels)
    
    logger.info("Clustering pipeline completed successfully!")


if __name__ == "__main__":
    main()



