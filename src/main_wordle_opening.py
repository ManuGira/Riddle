import pandas as pd
import urllib.request
from pathlib import Path
from ortools.linear_solver import pywraplp
import numpy as np
import common as cmn


def clean_accents(words: list[str]) -> list[str]:
    joined_words = ",".join(words)
    accent_to_base_char_map = cmn.load_accent_to_base_map()
    for accent_char, base_char in accent_to_base_char_map.items():
        joined_words = joined_words.replace(accent_char, base_char)
    return joined_words.split(",")


def filter_words(words: list[str], L: int) -> list[str]:
    # keep only words with N distinct letters.
    # No special characters
    # Lowercase letters only (no names)
    def is_valid(word):
        return (
                len(word) == L
                and len(set(word)) == L
                and all(c.isalpha() for c in word)
                and all(c.islower() for c in word)
        )
    valid_words = [w for w in words if is_valid(w)]
    return valid_words

def compute_word_entropies(words: list[str], frequency_map: dict[str, float]) -> pd.DataFrame:
    entropy_map = {c: -freq * np.log(freq) for c, freq in frequency_map.items() if freq > 0}

    df_words = pd.DataFrame({
        "word": words,
        "letters": [set(w) for w in words],
        "frequency": [sum(frequency_map.get(c, 0) for c in w) for w in words],
        "entropy": [sum(entropy_map[c] for c in w) for w in words],
    })
    return df_words

def find_word_with_different_letters(selected_words: list[str], word_list: list[str], N: int):
    if len(selected_words) == N:
        yield selected_words
        return
    for i, word in enumerate(word_list):
        if all(len(set(word) & set(sw)) == 0 for sw in selected_words):
            yield from find_word_with_different_letters(selected_words + [word], word_list[i + 1:], N)


def find_best_word_combination_brute_force(df_words: pd.DataFrame, N: int, metric: str):
    # get sorted list of sorted words by metric (entropy or frequency)
    words = df_words.sort_values(by=metric, ascending=False)["word"].tolist()
    solutions = []

    for solution in find_word_with_different_letters([], words, N=N):
        metric_score = sum(df_words[df_words["word"] == w][metric].values[0] for w in solution)
        solutions.append((metric_score, solution))

    # sort solutions by metric_score
    solutions = sorted(solutions, key=lambda x: x[0], reverse=True)
    print(f"Top solutions by {metric}:")
    for i, solution in enumerate(solutions):
        metric_score, solution = solution
        print(f"metric={metric_score:.2f}: ({', '.join(solution)})")
        if i >= 10:
            break
    print()




def find_best_word_combination(df_words: pd.DataFrame, N:int, letters: list[str]):

    # =========================
    # 3. ILP avec OR-Tools
    # =========================
    solver = pywraplp.Solver.CreateSolver("SCIP")
    assert solver is not None

    x = {i: solver.BoolVar(f"x_{i}") for i in df_words.index}

    # Constraints: N words
    solver.Add(sum(x[i] for i in x) == N)

    # Constraints: distinct letters
    for letter in letters:
        solver.Add(
            sum(
                x[i]
                for i, word_letters in df_words["letters"].items()
                if letter in word_letters
            ) <= 1
        )

    # objective, maximize total entropy
    # solver.Maximize(
    #     sum(df_words.loc[i, "entropy"] * x[i] for i in x)
    # )
    solver.Maximize(
        sum(df_words.loc[i, "frequency"] * x[i] for i in x)
    )

    status = solver.Solve()

    # =========================
    # 4. Résultat
    # =========================

    if status == pywraplp.Solver.OPTIMAL:
        solution = df_words.loc[
            [i for i in x if x[i].solution_value() == 1]
        ]
        print("Optimal words: ", list(solution["word"]))
        print("Total score :", solution["entropy"].sum())
    else:
        print("No optimal solution found.")


def find_best_opening(language: str, length: int, N: int, blacklist: list[str]):
    """
    Find the best opening words for Wordle-like games.
    :param language: "french" or "english"
    :param length: length of each word, depending on the game rule, e.g. 5 or 6
    :param N: number of words to select, depending on your strategy
    :param blacklist: list of words to exclude
    :return:
    """

    print(f"Loading {language} words of {length} distinct letters...")
    words = cmn.load_all_words(language)
    words = clean_accents(words)
    words = filter_words(words, length)
    words = [w for w in words if w not in blacklist]
    print(f"Number of valid words: {len(words)}")

    # compute frequency map
    frequency_map = cmn.compute_letter_frequency(words)

    # load frequency map
    # frequency_map = cmn.merge_accented_letter_frequency(cmn.load_letters_frequency(language), cmn.load_accent_to_base_map())

    # print N*L most frequent letters
    sorted_letters = sorted(frequency_map.items(), key=lambda item: item[1], reverse=True)
    print(f"{N*length} most frequent letters:", " ".join([item[0] for item in sorted_letters[:N*length]]))

    df_words = compute_word_entropies(words, frequency_map)
    letters = list(frequency_map.keys())

    # find_best_word_combination_brute_force(df_words, N, metric="frequency")
    # find_best_word_combination_brute_force(df_words, N, metric="entropy")
    find_best_word_combination(df_words, N, letters)


if __name__ == "__main__":
    find_best_opening("french", length=5, N=2, blacklist="anlet,irous,luteo,altin,astel,doylt,cothy,undim,harst,notus,autre,insol,aleut,abdom".split(","))
    # french, length=6, N=2: amours, client
    # french, length=6, N=3: dragon, mythes, public
    # french, length=6, N=2: etron, laius
    # french, length=5, N=3: abces, lundi, rompt
    # french, length=5, N=4: clamp, hebdo, jurys, vingt

    # english, length=5, N=2: ultra, noise
    # english, length=5, N=3: duchy, slain, trope
    # english, length=5, N=4: blank, crest, dough, wimpy
