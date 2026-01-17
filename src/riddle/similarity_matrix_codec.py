from riddle import DATA_FOLDER_PATH
from riddle import common as cmn
import numpy as np
from pathlib import Path
from abc import ABC, abstractmethod


class ISimilarityMatrixCodec(ABC):
    """Abstract base class for similarity matrix codecs."""
    
    @abstractmethod
    def encode(self, sim_matrix: np.ndarray, words: list[str]) -> dict:
        """
        Encode similarity matrix into a dictionary ready for saving.
        
        Args:
            sim_matrix: The computed similarity matrix
            words: List of words
        
        Returns:
            Dictionary with encoded data and metadata
        """
        raise NotImplementedError("encode must be implemented by subclass")
    
    @abstractmethod
    def decode(self, data: dict) -> tuple[np.ndarray, list[str]]:
        """
        Decode similarity matrix from loaded data.
        
        Args:
            data: Dictionary containing the loaded data
        
        Returns:
            Tuple of (similarity_matrix, words)
        """
        raise NotImplementedError("decode must be implemented by subclass")
    
    @staticmethod
    @abstractmethod
    def get_format_type() -> str:
        """
        Get the format type identifier for this codec.
        
        Returns:
            Format type string
        """
        raise NotImplementedError("get_format_type must be implemented by subclass")


class FullPrecisionMatrixCodec(ISimilarityMatrixCodec):
    """Encodes and decodes full precision (float64) similarity matrix."""
    
    @staticmethod
    def get_format_type() -> str:
        return 'full_precision'
    
    def encode(self, sim_matrix: np.ndarray, words: list[str]) -> dict:
        """
        Encode full precision similarity matrix.
        
        Args:
            sim_matrix: The computed similarity matrix
            words: List of words
        
        Returns:
            Dictionary with matrix, words, and format_type
        """
        return {
            'matrix': sim_matrix,
            'words': words,
            'format_type': self.get_format_type()
        }
    
    def decode(self, data: dict) -> tuple[np.ndarray, list[str]]:
        """
        Decode full precision similarity matrix.
        
        Args:
            data: Dictionary containing the loaded data
        
        Returns:
            Tuple of (similarity_matrix, words)
        """
        sim_matrix = data['matrix']
        words = data['words'].tolist() if hasattr(data['words'], 'tolist') else data['words']
        return sim_matrix, words


class LowPrecisionMatrixCodec(ISimilarityMatrixCodec):
    """Encodes and decodes low precision (uint8) similarity matrix."""
    
    @staticmethod
    def get_format_type() -> str:
        return 'low_precision'
    
    def encode(self, sim_matrix: np.ndarray, words: list[str]) -> dict:
        """
        Encode low precision (uint8) similarity matrix.
        
        Args:
            sim_matrix: The computed similarity matrix
            words: List of words
        
        Returns:
            Dictionary with encoded matrix, words, and format_type
        """
        sim_matrix_u8 = np.clip(((sim_matrix+1)/2*255), 0, 255).round().astype(np.uint8)
        return {
            'matrix': sim_matrix_u8,
            'words': words,
            'format_type': self.get_format_type()
        }
    
    def decode(self, data: dict) -> tuple[np.ndarray, list[str]]:
        """
        Decode low precision similarity matrix.
        
        Args:
            data: Dictionary containing the loaded data
        
        Returns:
            Tuple of (similarity_matrix_u8, words)
        """
        sim_matrix_u8 = data['matrix']
        words = data['words'].tolist() if hasattr(data['words'], 'tolist') else data['words']
        return sim_matrix_u8, words


class SparseMatrixCodec(ISimilarityMatrixCodec):
    """Encodes and decodes sparse (uint8) similarity matrix."""
    
    def __init__(self, percentile: float = 95.0):
        """
        Initialize sparse matrix codec.
        
        Args:
            percentile: Percentile threshold for keeping similarity values (default: 95.0)
        """
        self.percentile = percentile
    
    @staticmethod
    def get_format_type() -> str:
        return 'sparse'
    
    def encode(self, sim_matrix: np.ndarray, words: list[str]) -> dict:
        """
        Encode sparse similarity matrix (top percentile values only).
        
        Args:
            sim_matrix: The computed similarity matrix
            words: List of words
        
        Returns:
            Dictionary with encoded sparse data and metadata
        """
        # Get indexes i,j where sim_matrix[i,j] > top percentile of similarities
        vmin = np.percentile(sim_matrix, self.percentile)
        indices = np.where(sim_matrix >= vmin)
        # Remove indices where i >= j to keep only upper triangular part
        mask = indices[0] < indices[1]
        indices = (indices[0][mask], indices[1][mask])
        values = sim_matrix[indices]
        
        # Handle edge case where no values meet the threshold
        if len(values) == 0:
            vmax = vmin
            delta = 1.0  # Avoid division by zero
            encoded_values = np.array([], dtype=np.uint8)
        else:
            vmax = values.max()
            delta = vmax - vmin
            if delta == 0:
                # All values are the same
                encoded_values = np.full(len(values), 127, dtype=np.uint8)
            else:
                encoded_values = np.clip(((values-vmin)/delta*255).round(), 0, 255).astype(np.uint8)
        
        return {
            'indices': indices,
            'values': encoded_values,
            'words': words,
            'vmin': vmin,
            'vmax': vmax,
            'format_type': self.get_format_type()
        }
    
    def decode(self, data: dict) -> tuple[np.ndarray, list[str]]:
        """
        Decode sparse similarity matrix and reconstruct the full matrix.
        
        Args:
            data: Dictionary containing the loaded data
        
        Returns:
            Tuple of (similarity_matrix, words)
        """
        indices = tuple(data['indices'])
        values = data['values']
        words = data['words'].tolist() if hasattr(data['words'], 'tolist') else data['words']
        vmin = float(data['vmin'])
        vmax = float(data['vmax'])
        
        # Reconstruct the full similarity matrix
        N = len(words)
        sim_matrix = np.zeros((N, N), dtype=np.float64)
        
        # Denormalize uint8 values back to original similarity range
        delta = vmax - vmin
        denormalized_values = (values.astype(np.float64) / 255.0) * delta + vmin
        
        # Fill upper triangular part
        sim_matrix[indices] = denormalized_values
        
        # Make symmetric (since we only stored upper triangular)
        sim_matrix = sim_matrix + sim_matrix.T
        
        # Fill diagonal with 1.0 (self-similarity)
        np.fill_diagonal(sim_matrix, 1.0)
        
        return sim_matrix, words


def save_similarity_matrix(codec: ISimilarityMatrixCodec, sim_matrix: np.ndarray, words: list[str], filepath: Path):
    """
    Save similarity matrix using the specified codec.
    
    Args:
        codec: The codec to use for encoding
        sim_matrix: The computed similarity matrix
        words: List of words
        filepath: Full path to the output file
    """
    encoded_data = codec.encode(sim_matrix, words)
    if filepath.parent.exists() is False:
        filepath.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(filepath, **encoded_data)
    print(f"Similarity matrix saved to {filepath}.")


def load_similarity_matrix(filepath: Path, codec: ISimilarityMatrixCodec = None) -> tuple[np.ndarray, list[str]]:
    """
    Load similarity matrix from file. If codec is not provided, automatically detects the format type.
    
    Args:
        filepath: Full path to the input file
        codec: Optional codec to use for decoding. If None, auto-detects from format_type
    
    Returns:
        Tuple of (similarity_matrix, words)
    """
    data = np.load(filepath, allow_pickle=True)
    
    if codec is None:
        # Auto-detect codec from format_type
        if 'format_type' not in data:
            raise ValueError(f"File {filepath} does not contain format_type metadata. Cannot determine loader.")
        
        format_type = str(data['format_type'])
        
        if format_type == 'full_precision':
            codec = FullPrecisionMatrixCodec()
        elif format_type == 'low_precision':
            codec = LowPrecisionMatrixCodec()
        elif format_type == 'sparse':
            codec = SparseMatrixCodec()
        else:
            raise ValueError(f"Unknown format_type: {format_type}")
    
    # Convert numpy archive to dict
    data_dict = {key: data[key] for key in data.files}
    
    sim_matrix, words = codec.decode(data_dict)
    print(f"Similarity matrix loaded from {filepath}.")
    return sim_matrix, words


def main(D, N: int = None):
    print("Loading model...")

    model_files = {
        200: f"frWac_non_lem_no_postag_no_phrase_200_cbow_cut100.bin",
        700: f"frWiki_no_phrase_no_postag_700_cbow_cut100.bin",
    }

    model = cmn.load_model(model_files[D])

    print("Loading words...")
    words = cmn.load_most_frequent_words(N=N, model=model)
    N = len(words)
    print(f"Loaded {N} words.")

    output_folder = DATA_FOLDER_PATH / "similarity_matrices"

    sim_matrix = cmn.compute_similarity_matrix_fast(model, words)

    # Generate all three types of matrices using the dedicated classes
    full_precision_file = output_folder / f"similarity_matrix_N{N}f64_D{D}_c.npz"
    save_similarity_matrix(FullPrecisionMatrixCodec(), sim_matrix, words, full_precision_file)
    
    low_precision_file = output_folder / f"similarity_matrix_N{N}u8_D{D}_c.npz"
    save_similarity_matrix(LowPrecisionMatrixCodec(), sim_matrix, words, low_precision_file)
    
    percentile = 95
    sparse_file = output_folder / f"similarity_matrix_sparse_p{percentile}_N{N}u8_D{D}_c.npz"
    save_similarity_matrix(SparseMatrixCodec(percentile=percentile), sim_matrix, words, sparse_file)
    

if __name__ == '__main__':
    main(200, N=None)
    # main(200)
    # for d in [200, 700]:
    #     for n in [10, 100, 1000, 5000]:
    #         print(f"Generating similarity matrices for D={d}, N={n}...")
    #         main(d, N=n)
