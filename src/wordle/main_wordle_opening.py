import pandas as pd
from ortools.linear_solver import pywraplp
import numpy as np
import argparse
import riddle.common as cmn
from riddle import Language, DATA_FOLDER_PATH
from pathlib import Path
import csv


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


def initialize_csv_file(csv_path: Path) -> None:
    """Initialize CSV file with headers if it doesn't exist."""
    if not csv_path.exists():
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['frequency_score', 'words'])


def load_existing_solutions(csv_path: Path, df_words: pd.DataFrame, N: int) -> tuple[int, list[list[int]]]:
    """
    Load existing solutions from CSV file and return start iteration and excluded combinations.
    
    :param csv_path: Path to the CSV file
    :param df_words: DataFrame containing word data
    :param N: Number of words per combination
    :return: Tuple of (start_iteration, excluded_combinations)
    """
    if not csv_path.exists():
        return 0, []
    
    print(f"Loading existing solutions from {csv_path.name}...")
    existing_df = pd.read_csv(csv_path)
    start_iteration = len(existing_df)
    print(f"Found {start_iteration} existing solutions. Continuing from rank {start_iteration + 1}...")
    
    # Reconstruct excluded combinations from CSV
    excluded_combinations = []
    for _, row in existing_df.iterrows():
        words = row['words'].split(', ')
        word_indices = [df_words[df_words['word'] == word].index[0] for word in words if word in df_words['word'].values]
        if len(word_indices) == N:
            excluded_combinations.append(word_indices)
    
    return start_iteration, excluded_combinations


def append_solution_to_csv(csv_path: Path, frequency_score: float, words: list[str]) -> None:
    """
    Append a solution to the CSV file.
    
    :param csv_path: Path to the CSV file
    :param frequency_score: The frequency score of the solution
    :param words: List of words in the solution
    """
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            f"{frequency_score:.4f}",
            ', '.join(words)
        ])


def find_word_with_different_letters(selected_words: list[str], word_list: list[str], N: int):
    if len(selected_words) == N:
        yield selected_words
        return
    for i, word in enumerate(word_list):
        if all(len(set(word) & set(sw)) == 0 for sw in selected_words):
            yield from find_word_with_different_letters(selected_words + [word], word_list[i + 1:], N)


def find_best_word_combination(df_words: pd.DataFrame, N:int, letters: list[str], frequency_map: dict[str, float], top_k: int = 1, csv_path: Path = None):

    solutions = []
    start_iteration = 0
    excluded_combinations = []
    
    # Load existing solutions and initialize CSV if needed
    if csv_path:
        initialize_csv_file(csv_path)
        start_iteration, excluded_combinations = load_existing_solutions(csv_path, df_words, N)
    
    for iteration in range(start_iteration, start_iteration + top_k):
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

        # Exclude previously found solutions
        for excluded_indices in excluded_combinations:
            # At least one word must be different from this previous solution
            solver.Add(sum(x[i] for i in excluded_indices) <= N - 1)

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
            selected_indices = [i for i in x if x[i].solution_value() == 1]
            solution = df_words.loc[selected_indices]
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

            solution_data = {
                'rank': iteration + 1,
                'words': selected_words,
                'distinct_letter_count': distinct_letter_count,
                'all_letters': sorted(all_letters),
                'frequency_score': total_frequency,
                'unique_positions': int(unique_position_count),
                'position_overlaps': position_overlaps
            }
            solutions.append(solution_data)
            
            # Save to CSV immediately
            if csv_path:
                append_solution_to_csv(csv_path, total_frequency, selected_words)
                print(f"[Saved to CSV] Rank #{iteration + 1}: {', '.join(selected_words)}")
            
            # Store this combination to exclude it in next iteration
            excluded_combinations.append(selected_indices)
        else:
            # No more solutions found
            break
    
    # Print all solutions
    if solutions:
        print(f"\n{'='*80}")
        print(f"Found {len(solutions)} optimal word combinations:")
        print(f"{'='*80}\n")
        
        for sol in solutions:
            print(f"Rank #{sol['rank']}:")
            print(f"  Words: {', '.join(sol['words'])}")
            print(f"  Distinct letters: {sol['distinct_letter_count']} ({', '.join(sol['all_letters'])})")
            print(f"  Frequency score: {sol['frequency_score']:.4f}")
            print(f"  Unique positions: {sol['unique_positions']}")
            if sol['position_overlaps']:
                print("  Position overlaps:")
                for pos, letter, words in sol['position_overlaps']:
                    print(f"    Position {pos}: '{letter}' in {words}")
            print(f"  | {len(sol['words'][0])} | {N} | {', '.join(sol['words'])} |")
            print()
    else:
        print("No optimal solution found.")


def find_best_opening(language: Language, length: int, N: int, top_k: int = 1):
    """
    Find the best opening words for Wordle-like games.
    :param language: "french" or "english"
    :param length: length of each word, depending on the game rule, e.g. 5 or 6
    :param N: number of words to select, depending on your strategy
    :param top_k: number of top solutions to find (default: 1)
    :return:
    """
    
    # Create CSV filename with parameters
    csv_filename = f"wordle_openings_{language.value}_L{length}_N{N}_top{top_k}.csv"
    csv_path = DATA_FOLDER_PATH / "results" / csv_filename
    print(f"Results will be saved to: {csv_path}")

    print(f"Loading {language} words of {length} distinct letters...")

    # load words from data/words_lists/wordle_list_{language}_L{length}_base.txt
    words_file = DATA_FOLDER_PATH / "words_lists" / f"wordle_list_{language.lower()}_L{length}_base.txt"
    with open(words_file, encoding="utf-8") as f:
        words = [w.strip() for w in f if w.strip()]

    print(f"Number  words: {len(words)}")

    # compute frequency map
    frequency_map = cmn.compute_letter_frequency(words)

    # load frequency map
    # frequency_map = cmn.merge_accented_letter_frequency(cmn.load_letters_frequency(language), cmn.load_accent_to_base_map())

    # print N*L most frequent letters
    sorted_letters = sorted(frequency_map.items(), key=lambda item: item[1], reverse=True)
    print(f"{N*length} most frequent letters:", " ".join([item[0] for item in sorted_letters[:N*length]]))

    df_words = compute_word_entropies(words, frequency_map)
    letters = list(frequency_map.keys())

    find_best_word_combination(df_words, N, letters, frequency_map, top_k, csv_path)



if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Find the best opening words for Wordle-like games using letter frequency analysis."
    )
    parser.add_argument(
        "language",
        type=str,
        choices=["fr", "en"],
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
    parser.add_argument(
        "--top-k",
        type=int,
        default=1,
        help="Number of top solutions to find (default: 1)"
    )

    args = parser.parse_args()


    find_best_opening(Language(args.language.upper()), args.length, args.N, args.top_k)

    # french, length=6, N=2: amours, client
    # french, length=6, N=3: dragon, mythes, public
    # french, length=6, N=2: etron, laius
    # french, length=5, N=3: abces, lundi, rompt
    # french, length=5, N=4: clamp, hebdo, jurys, vingt

    # english, length=5, N=2: ultra, noise
    # english, length=5, N=3: duchy, slain, trope
    # english, length=5, N=4: blank, crest, dough, wimpy
