import os
import numpy as np
from os.path import join as pjoin
from gensim.models import KeyedVectors



def load_most_frequent_words(N: int = None, model=None):
    here = os.path.abspath(os.path.dirname(__file__))
    data_folder = pjoin(here, "..", "data")
    freq_file = pjoin(data_folder, "frequency.txt")

    with open(freq_file, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f.readlines()]

    words = [word.replace("œ", "oe") for word in words]  # replace œ with oe
    words = [word for word in words if "'" not in word]  # remove words with apostrophes
    UNKNOWN_WORDS = "un le de ne ce ou où plusieurs lequel selon".split()  # unknonw words to remove
    words = [word for word in words if word not in UNKNOWN_WORDS]
    words = [word for word in words if len(word) >= 2] # min length 2

    if model is not None:
        words = [word for word in words if word in model.key_to_index]

    if N is None:
        return words

    N = min(N, len(words))
    return words[:N]


def load_model(model_file="frWac_non_lem_no_postag_no_phrase_200_cbow_cut100.bin"):
    here = os.path.abspath(os.path.dirname(__file__))
    data_folder = pjoin(here, "..", "data")
    model_path = pjoin(data_folder, model_file)

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
        for j in range(N):
            correlation_matrix[i, j] = np.dot(vectors[i], vectors[j]) / (
                np.linalg.norm(vectors[i]) * np.linalg.norm(vectors[j])
            )
    return correlation_matrix


def compute_distance_matrix(model, words):
    indexes = [model.key_to_index[word] for word in words if word in model.key_to_index]
    vectors = [model.vectors[index] for index in indexes]
    N = len(vectors)
    distance_matrix = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            distance_matrix[i, j] = np.linalg.norm(vectors[i] - vectors[j])
    return distance_matrix


def compute_similarity_matrix(model, words):
    indexes = [model.key_to_index[word] for word in words if word in model.key_to_index]
    vectors = [model.vectors[index] for index in indexes]
    N = len(vectors)
    similarity_matrix = np.zeros((N, N))
    for i in range(N):
        for j in range(N):
            similarity_matrix[i, j] = model.similarity(words[i], words[j])
    return similarity_matrix


def compute_heatmap_matrix(model, words):
    # Convert similarities to heat
    return compute_similarity_matrix(model, words) * 100


