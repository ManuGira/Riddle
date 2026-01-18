import pandas as pd
from ortools.linear_solver import pywraplp
import numpy as np
import argparse
import riddle.common as cmn


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




def find_best_word_combination(df_words: pd.DataFrame, N:int, letters: list[str], frequency_map: dict[str, float]):

    # =========================
    # 3. ILP avec OR-Tools
    # =========================
    solver = pywraplp.Solver.CreateSolver("SCIP")
    assert solver is not None

    x = {i: solver.BoolVar(f"x_{i}") for i in df_words.index}
    
    # For each letter, create a binary variable indicating if it's used at least once
    y = {letter: solver.BoolVar(f"y_{letter}") for letter in letters}

    # Constraints: N words
    solver.Add(sum(x[i] for i in x) == N)

    # For each letter, y[letter] = 1 if at least one selected word contains that letter
    for letter in letters:
        words_with_letter = [
            i for i, word_letters in df_words["letters"].items()
            if letter in word_letters
        ]
        if words_with_letter:
            # If any word containing this letter is selected, y[letter] can be 1
            solver.Add(y[letter] <= sum(x[i] for i in words_with_letter))
            # Force y[letter] to be 1 if any word with this letter is selected
            for i in words_with_letter:
                solver.Add(y[letter] >= x[i])

    # Create binary variables for each (letter, position) pair to track unique positions
    # z[letter][pos] = 1 if letter appears at position pos in exactly one selected word
    max_word_length = df_words["word"].str.len().max()
    z = {}
    for letter in letters:
        z[letter] = {}
        for pos in range(max_word_length):
            z[letter][pos] = solver.BoolVar(f"z_{letter}_{pos}")
            
            # Find words that have this letter at this position
            words_with_letter_at_pos = [
                i for i, word in df_words["word"].items()
                if len(word) > pos and word[pos] == letter
            ]
            
            if words_with_letter_at_pos:
                # Ensure at most one word with this letter at this position is selected
                solver.Add(sum(x[i] for i in words_with_letter_at_pos) <= 1)
                # z[letter][pos] = 1 if and only if exactly one matching word is selected
                # Since we already constrain sum <= 1, we can use equality
                solver.Add(z[letter][pos] == sum(x[i] for i in words_with_letter_at_pos))
            else:
                # No words have this letter at this position, z must be 0
                solver.Add(z[letter][pos] == 0)

    # Objective: maximize the sum of frequencies of distinct letters used
    # Plus a small bonus (1/1000) for each unique (letter, position) pair
    position_bonus = 0.001
    solver.Maximize(
        sum(frequency_map[letter] * y[letter] for letter in letters) +
        position_bonus * sum(z[letter][pos] for letter in letters for pos in range(max_word_length))
    )

    status = solver.Solve()

    # =========================
    # 4. Résultat
    # =========================

    if status == pywraplp.Solver.OPTIMAL:
        solution = df_words.loc[
            [i for i in x if x[i].solution_value() == 1]
        ]
        selected_words = list(solution["word"])
        all_letters = set()
        for word in selected_words:
            all_letters.update(word)
        distinct_letter_count = len(all_letters)
        total_frequency = sum(frequency_map[letter] for letter in all_letters)
        
        # Calculate unique position count
        unique_position_count = sum(
            z[letter][pos].solution_value() 
            for letter in letters 
            for pos in range(max_word_length)
        )
        
        # Find position overlaps for reporting
        position_overlaps = []
        for pos in range(max_word_length):
            letter_at_pos = {}
            for word in selected_words:
                if pos < len(word):
                    letter = word[pos]
                    if letter not in letter_at_pos:
                        letter_at_pos[letter] = []
                    letter_at_pos[letter].append(word)
            for letter, words in letter_at_pos.items():
                if len(words) > 1:
                    position_overlaps.append((pos, letter, words))
        
        print("Optimal words: ", selected_words)
        print(f"Distinct letters: {distinct_letter_count} ({', '.join(sorted(all_letters))})")
        print(f"Total frequency score: {total_frequency:.4f}")
        print(f"Unique letter positions: {int(unique_position_count)}")
        if position_overlaps:
            print("Position overlaps:")
            for pos, letter, words in position_overlaps:
                print(f"  Position {pos}: '{letter}' in {words}")
    else:
        print("No optimal solution found.")


def find_best_opening(language: str, length: int, N: int):
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
    find_best_word_combination(df_words, N, letters, frequency_map)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Find the best opening words for Wordle-like games using letter frequency analysis."
    )
    parser.add_argument(
        "language",
        type=str,
        choices=["french", "english"],
        help="Language to use: french or english"
    )
    parser.add_argument(
        "length",
        type=int,
        help="Length of each word"
    )
    parser.add_argument(
        "N",
        type=int,
        help="Number of opening words to select"
    )

    args = parser.parse_args()

    find_best_opening(args.language, args.length, args.N)

    # french, length=6, N=2: amours, client
    # french, length=6, N=3: dragon, mythes, public
    # french, length=6, N=2: etron, laius
    # french, length=5, N=3: abces, lundi, rompt
    # french, length=5, N=4: clamp, hebdo, jurys, vingt

    # english, length=5, N=2: ultra, noise
    # english, length=5, N=3: duchy, slain, trope
    # english, length=5, N=4: blank, crest, dough, wimpy
