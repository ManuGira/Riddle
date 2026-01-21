import dataclasses
import json
import time
import urllib.request
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from gensim.models import KeyedVectors

from pathlib import Path

def repo_root_path() -> Path:
    """Get the root path of the riddle repo."""
    repo_root = Path(__file__).parent
    # Look for pyproject.toml
    while not (repo_root / "pyproject.toml").exists():
        repo_root = repo_root.parent
        # Safety: stop at filesystem root
        if repo_root == repo_root.parent:
            # Fallback: assume we're in src/riddle, so go up 2 levels
            return Path(__file__).parent.parent.parent
    return repo_root

REPO_ROOT_PATH: Path = repo_root_path()
DATA_FOLDER_PATH: Path = REPO_ROOT_PATH / "data"
STATIC_FOLDER_PATH: Path = REPO_ROOT_PATH / "src" / "static"


def unit_vector(vec: np.ndarray) -> np.ndarray:
    """
    Normalize a vector to unit length.
    
    Args:
        vec: Input vector
        
    Returns:
        Unit vector
    """
    norms = np.linalg.norm(vec, axis=1, keepdims=True)
    norms[norms == 0] = 1.0  # prevent division by
    return vec / norms

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity value
    """
    return np.dot(unit_vector(vec1), unit_vector(vec2))

def cosine_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Compute cosine distance between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine distance value
    """
    return 1.0 - cosine_similarity(vec1, vec2)

def load_most_frequent_words(N: int | None = None, model: "KeyedVectors | None" = None) -> list[str]:
    freq_file = DATA_FOLDER_PATH / "french_words_5000.txt"

    with open(freq_file, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f.readlines()]

    words = [word.replace("œ", "oe") for word in words]  # replace œ with oe
    words = [word for word in words if "'" not in word]  # remove words with apostrophes
    UNKNOWN_WORDS = "un le de ne ce ou où plusieurs lequel selon dont entre".split()  # unknonw words to remove
    words = [word for word in words if word not in UNKNOWN_WORDS]
    words = [word for word in words if len(word) >= 2] # min length 2

    if model is not None:
        words = [word for word in words if word in model.key_to_index]

    if N is None:
        return words

    N = min(N, len(words))
    if True:
        # pick N words evenly spaced in the list
        step = len(words) // N
        return [words[int(i * step)] for i in range(N)]
    return words[:N]


def load_model(model_file="frWac_non_lem_no_postag_no_phrase_200_cbow_cut100.bin"):    
    from gensim.models import KeyedVectors
    model_path = DATA_FOLDER_PATH / model_file

    model = KeyedVectors.load_word2vec_format(
        model_path,
        binary=True,
        unicode_errors="ignore",
    )
    return model


def compute_correlation_matrix(model, words):
    indexes = [model.key_to_index[word] for word in words if word in model.key_to_index]
    vectors = [model.vectors[index] for index in indexes]
    N = len(vectors)
    correlation_matrix = np.zeros((N, N))
    for i in range(N):
        for j in range(i, N):
            correlation_matrix[i, j] = np.dot(vectors[i], vectors[j]) / (
                np.linalg.norm(vectors[i]) * np.linalg.norm(vectors[j])
            )

    correlation_matrix = correlation_matrix + correlation_matrix.T - np.diag(correlation_matrix.diagonal())
    return correlation_matrix


def compute_distance_matrix(model, words):
    indexes = [model.key_to_index[word] for word in words if word in model.key_to_index]
    vectors = [model.vectors[index] for index in indexes]
    N = len(vectors)
    distance_matrix = np.zeros((N, N))
    for i in range(N):
        for j in range(i, N):
            distance_matrix[i, j] = np.linalg.norm(vectors[i] - vectors[j])

    distance_matrix = distance_matrix + distance_matrix.T - np.diag(distance_matrix.diagonal())
    return distance_matrix

def compute_similarity_matrix_fast(model, words):
    print("Computing similarity matrix (fast)...")
    indexes = [model.key_to_index[word] for word in words if word in model.key_to_index]
    vectors = np.array([model.vectors[index] for index in indexes])
    vectors = unit_vector(vectors)
    tick = time.time()
    similarity_matrix = np.dot(vectors, vectors.T)
    tock = time.time()
    print(f"Similarity matrix computed in {tock - tick:.2f} seconds.")
    return similarity_matrix

def compute_similarity_matrix(model, words):
    print("Computing similarity matrix...")
    indexes = [model.key_to_index[word] for word in words if word in model.key_to_index]
    vectors = [model.vectors[index] for index in indexes]
    N = len(vectors)
    similarity_matrix = np.zeros((N, N))
    tick = time.time()
    for i in range(N):
        for j in range(i, N):
            similarity_matrix[i, j] = model.similarity(words[i], words[j])

    similarity_matrix = similarity_matrix + similarity_matrix.T - np.diag(similarity_matrix.diagonal())

    tock = time.time()
    print(f"Similarity matrix computed in {tock - tick:.2f} seconds.")
    return similarity_matrix


def compute_heatmap_matrix(model, words):
    # Convert similarities to heat
    return compute_similarity_matrix(model, words) * 100

def load_accent_to_base_map() -> dict[str, str]:
    accent_file = DATA_FOLDER_PATH / "accent_to_base.json"
    with open(accent_file, "r", encoding="utf-8") as f:
        accent_to_base_map = json.load(f)
    return accent_to_base_map

def load_base_to_accents_map() -> dict[str, str]:
    """
    file is of the form:
        base,accents
        a,àâáåäãą
        ae,æ
        oe,œ
    ...

    :return:
    """
    accent_file = DATA_FOLDER_PATH / "base_to_accents.csv"
    base_to_accents_map = {}
    with open(accent_file, "r", encoding="utf-8") as f:
        f.readline()  # skip header
        for line in f.readlines():
            base, accents = line.strip().split(",")
            base_to_accents_map[base] = accents
    return base_to_accents_map

def load_letters_frequency(language:str) -> dict[str, float]:
    """
    file is of the form:
    letter,english,french,german,spanish,portuguese,esperanto,italian,turkish,swedish,polish,dutch,danish,icelandic,finnish,czech,lithuanian
    a,0.0817,0.0764,0.0652,0.1253,0.1463,0.1212,0.1174,0.1192,0.0938,0.0891,0.0749,0.0603,0.1011,0.1222,0.0817,0.1119
    b,0.0149,0.0090,0.0189,0.0142,0.0104,0.0098,0.0093,0.0284,0.0153,0.0147,0.0158,0.0200,0.0104,0.0028,0.0082,0.0148
    c,0.0278,0.0326,0.0306,0.0468,0.0388,0.0078,0.0450,0.0096,0.0149,0.0396,0.0124,0.0056,0.0000,0.0028,0.0074,0.0060
    d,0.0425,0.0367,0.0508,0.0581,0.0499,0.0304,0.0374,0.0471,0.0470,0.0325,0.0593,0.0586,0.0158,0.0104,0.0348,0.0258
    ... (more lines) ...
    :param language:
    :return:
    """
    freq_file = DATA_FOLDER_PATH / "letters_frequency.csv"

    frequency_map = {}
    with open(freq_file, "r", encoding="utf-8") as f:
        header = f.readline().strip().split(",")
        assert language in header, f"Language '{language}' not found in frequency file."
        lang_index = header.index(language)
        for line in f.readlines():
            frequencies = line.strip().split(",")
            letter = frequencies[0]
            freq = float(frequencies[lang_index])
            frequency_map[letter] = float(freq)

    return frequency_map

def merge_accented_letter_frequency(letters_frequency: dict[str, float], accent_to_base_map: dict[str, str]) -> dict[str, float]:
    """
    Merge frequencies of accented letters into their base letters.
    Creating a new frequency map, with fewer letters and higher frequencies.
    :param accent_to_base_map:
    :return:
    """
    letters_frequency = letters_frequency.copy()
    for accent, base in accent_to_base_map.items():
        if accent not in letters_frequency:
            continue
        if base not in letters_frequency:
            letters_frequency[base] = 0.0

        letters_frequency[accent] += letters_frequency[accent]
        del letters_frequency[accent]

    letters_frequency = {letter: freq for letter, freq in letters_frequency.items() if freq > 0.0}

    return letters_frequency


def load_all_words(language: str) -> list[str]:
    """
    Load a list of words for the specified language.
    :param language: Language code (e.g., "french", "english")
    :return: List of words
    """
    @dataclasses.dataclass
    class LexiconFile:
        filename: str
        url: str

    lexicon_file = {
        "french": LexiconFile(
            filename="french_words.txt",
            url="https://raw.githubusercontent.com/Taknok/French-Wordlist/master/francais.txt",
        ),
        "english": LexiconFile(
            filename="english_words.txt",
            url="https://people.sc.fsu.edu/~jburkardt/datasets/words/wordle.txt",
        ),
    }

    lexicon_path = DATA_FOLDER_PATH / lexicon_file[language].filename

    if not lexicon_path.exists():
        print("Downloading the lexicon...")
        urllib.request.urlretrieve(lexicon_file[language].url, lexicon_path)

    with open(lexicon_path, encoding="utf-8") as f:
        words = [w.strip() for w in f]
    return words


def compute_letter_frequency(words: list[str]) -> dict[str, float]:
    """
    Compute letter frequency in a list of words.
    :param words:
    :return:
    """
    letter_histogram: dict[str, int] = {}
    for word in words:
        for letter in set(word):
            letter_histogram[letter] = letter_histogram.get(letter, 0) + 1
    count = sum(letter_histogram.values())
    letter_frequency = {k: v / count for k, v in letter_histogram.items()}
    return letter_frequency


def compute_positional_letter_frequency(words: list[str]) -> list[dict[str, float]]:
    """
    Compute letter frequency for each position in words.
    Returns a list of frequency maps, one for each position (0 to max_word_length-1).
    
    :param words: List of words to analyze
    :return: List of dictionaries, where each dict maps letter -> frequency at that position
    """
    if not words:
        return []
    
    max_length = max(len(word) for word in words)
    frequency_maps = []
    
    for pos in range(max_length):
        letter_histogram: dict[str, int] = {}
        word_count_at_pos = 0
        
        for word in words:
            if pos < len(word):
                letter = word[pos]
                letter_histogram[letter] = letter_histogram.get(letter, 0) + 1
                word_count_at_pos += 1
        
        # Compute frequency for this position
        if word_count_at_pos > 0:
            frequency_map = {letter: count / word_count_at_pos 
                           for letter, count in letter_histogram.items()}
        else:
            frequency_map = {}
        
        frequency_maps.append(frequency_map)
    
    return frequency_maps


def compute_positional_letter_entropy(words: list[str]) -> list[dict[str, float]]:
    """
    Compute letter entropy for each position in words.
    Entropy = -p * log2(p), which represents information content
    
    :param words: List of words to analyze
    :return: List of dictionaries, where each dict maps letter -> entropy at that position
    """
    import math
    
    if not words:
        return []
    
    # First get frequencies
    frequency_maps = compute_positional_letter_frequency(words)
    
    # Convert frequencies to entropy
    entropy_maps = []
    for freq_map in frequency_maps:
        entropy_map = {}
        for letter, freq in freq_map.items():
            if freq > 0:
                # Entropy = -p * log2(p)
                entropy_map[letter] = -freq * math.log2(freq)
            else:
                entropy_map[letter] = 0.0
        entropy_maps.append(entropy_map)
    
    return entropy_maps