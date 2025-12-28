import os
import time
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from os.path import join as pjoin
import zlib

from common import load_model, load_most_frequent_words, compute_heatmap_matrix


def plot_matrix(correlation_matrix, words):
    plt.figure(figsize=(8, 6))
    sns.heatmap(correlation_matrix, xticklabels=words, yticklabels=words, annot=True, cmap="coolwarm")
    plt.title("Word Distance Matrix")
    plt.show()


class GameAssistant:
    def __init__(self, heatmap_matrix, words):
        self.heatmap_matrix = heatmap_matrix
        self.all_words = [w for w in words]
        self.observed_words_score_map = {}
        self.next_suggestion = self.all_words[0]

    def compute_sub_matrix(self):
        observed_words = list(self.observed_words_score_map.keys())
        observed_indexes = [self.all_words.index(word) for word in observed_words]
        not_observed_indexes = [i for i in range(len(self.all_words)) if i not in observed_indexes]

        # Use np.ix_ to properly index rows and columns
        sub_matrix = self.heatmap_matrix[np.ix_(not_observed_indexes, observed_indexes)]
        return sub_matrix

    def compute_word_probabilities(self):
        """
        Compute probability for each word to be the secret word based on observed rankings.

        Args:
            words: list of all N words
            observed_words: words already tested
            observed_scores: their corresponding scores -100 to 100, higher is better

        Returns:
            Tuple of (ranked_words, ranked_scores)
        """
        sub_matrix = self.compute_sub_matrix()

        # remove rows of observed words
        observed_words = list(self.observed_words_score_map.keys())
        observed_scores = np.array(list(self.observed_words_score_map.values()))
        remaining_words = [word for word in self.all_words if word not in observed_words]


        if False:
            # Divide by number of observed words to get average similarity
            sub_matrix = sub_matrix / len(observed_words)
            # L2 normalize observed scores
            observed_scores = observed_scores / np.sqrt(np.mean(observed_scores**2))
            suggestions_score = np.dot(sub_matrix, observed_scores)
        else:
            # RMSE approach
            err = (sub_matrix - observed_scores[np.newaxis, :])
            rmse = np.sqrt(np.mean(err**2, axis=1))
            # Convert RMSE to a score (lower RMSE -> higher score)
            suggestions_score = 100 - rmse

        # sort scores to get a ranked list of words
        ranked_indexes = np.argsort(-suggestions_score)
        ranked_scores = suggestions_score[ranked_indexes]
        ranked_words = [remaining_words[i] for i in ranked_indexes]

        return ranked_words, ranked_scores


    def add_word_score(self, word: str, score: float) -> tuple[list[str] | None, str]:
        """
        Add a word and its score, compute suggestions, and return the next suggestion.

        Args:
            word: The word that was tested
            score: The score received for that word (-100 to 100)

        Returns:
            Tuple of (next_suggestion, message_to_print)
            next_suggestion can be None if not enough data or no words available
        """
        if word not in self.all_words:
            msg = f"Word '{word}' not in the list. Please try again."
            return None, msg

        self.observed_words_score_map[word] = score

        msg = f"Observed '{word}' with score {score:.2f}\n"

        # Compute suggestions
        ranked_words, ranked_scores = self.compute_word_probabilities()

        if len(ranked_words) == 0:
            msg += "No more words available for suggestions."
            return None, msg

        # Build message with top 10 suggestions
        msg += "\nTop 10 suggestions:"
        for w, s in list(zip(ranked_words, ranked_scores))[:10]:
            msg += f"\n  {w}: {s:.4f}"

        self.next_suggestion = ranked_words[0]
        return self.next_suggestion, msg

    def run_interactive(self):
        """Interactive mode: ask user for input and print suggestions."""
        print("Game Assistant started")

        print(f"\nFirst suggestion: {self.next_suggestion}")

        while True:
            word = input("\nEnter observed word: ").strip()

            if word not in self.all_words:
                print(f"Word '{word}' not in the list. Please try again.")
                continue

            while True:
                try:
                    score = float(input(f"Enter score for '{word}': "))
                    break
                except ValueError:
                    print("Invalid input. Please enter a numeric score.")

            suggestion, msg = self.add_word_score(word, score)
            print(msg)

            if suggestion:
                print(f"\n→ Next suggestion: {suggestion}")

    def run_interactive_semi_auto(self):
        """Interactive mode: ask user for input and print suggestions."""
        print("Game Assistant started")
        print(f"\nFirst suggestion: {self.next_suggestion}")
        suggestion = self.next_suggestion
        while True:
            try:
                score = float(input(f"{suggestion}: "))
            except ValueError:
                print("Invalid input. Please enter a numeric score.")
                continue
            suggestion, msg = self.add_word_score(suggestion, score)

def compute_heatmap_matrix_if_needed(words: list[str]) -> tuple[np.ndarray, np.ndarray]:
    # compute heatmap matrix if not already saved
    N = len(words)
    # Compute crc32 of words list to use as cache key
    words_str = ",".join(words)
    words_crc32 = zlib.crc32(words_str.encode('utf-8')) & 0xffffffff

    here = os.path.abspath(os.path.dirname(__file__))
    cached_matrix_file = pjoin(here, "..", ".cache", f"heatmap_matrix_{N}_{words_crc32:x}_v2.npz")

    if os.path.exists(cached_matrix_file):
        print(f"Loading precomputed heatmap matrix: {cached_matrix_file}")
        npzfile = np.load(cached_matrix_file)
        heatmap_matrix = npzfile['arr_0']
        words = npzfile['arr_1']
    else:
        print("Loading model...")
        model = load_model()

        # ensure all words are in the model
        assert all([word in model.key_to_index for word in words])

        print("Computing heatmap matrix...")
        tick = time.time()
        heatmap_matrix = compute_heatmap_matrix(model, words)
        tock = time.time()
        print(f"Heatmap matrix computed in {tock - tick:.02f} seconds.")
        # save words and heatmap matrix for future use
        os.makedirs(os.path.dirname(cached_matrix_file), exist_ok=True)
        np.savez(cached_matrix_file, heatmap_matrix, words)
        print(f"Heatmap matrix saved to {cached_matrix_file}.")

    return heatmap_matrix, words


def main():
    N = 5000
    print(f"Using {N} words.")
    model = load_model()
    words = load_most_frequent_words(N, model)
    # words = ["roi", "reine", "banane", "pomme", "voiture", "camion", "avion", "bateau", "félin", "chat", "chien"]

    heatmap_matrix, words = compute_heatmap_matrix_if_needed(words)
    N = len(words)

    if N <= 50:
        print("Plotting correlation matrix...")
        plot_matrix(heatmap_matrix, words)

    print("Starting game assistant...")
    assistant = GameAssistant(heatmap_matrix, words)
    assistant.run_interactive_semi_auto()


if __name__ == "__main__":
    main()

