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


def compute_information_value(words: list[str], positional_entropy_maps: list[dict[str, float]]) -> float:
    """
    Compute the information value of a word combination, accounting for duplicate letters.
    Uses entropy (information content) rather than raw frequency.
    
    In Wordle:
    - First occurrence of a letter tells us: "this letter exists" + "at this position or elsewhere"
    - Subsequent occurrences only add positional information (reduced value)
    
    :param words: List of words in the combination
    :param positional_entropy_maps: List of entropy maps, one per position
    :return: Total information value (in bits)
    """
    letter_positions = {}  # letter -> list of positions where it appears
    
    # Collect all (letter, position) pairs across all words
    for word in words:
        for pos, letter in enumerate(word):
            if letter not in letter_positions:
                letter_positions[letter] = []
            letter_positions[letter].append(pos)
    
    total_value = 0.0
    
    for letter, positions in letter_positions.items():
        # For each unique letter:
        # - First occurrence gets full entropy value (information content)
        # - Additional occurrences get reduced value (only positional differentiation)
        
        # Sort positions to process them consistently
        sorted_positions = sorted(set(positions))  # unique positions only
        
        for i, pos in enumerate(sorted_positions):
            if pos < len(positional_entropy_maps):
                entropy_map = positional_entropy_maps[pos]
                if letter in entropy_map:
                    if i == 0:
                        # First occurrence: full entropy value
                        total_value += entropy_map[letter]
                    else:
                        # Additional occurrences: reduced value (30% for positional info)
                        # This is a heuristic - the reduction factor could be tuned
                        total_value += entropy_map[letter] * 0.3
    
    return total_value


def find_word_with_different_letters(selected_words: list[str], word_list: list[str], N: int):
    if len(selected_words) == N:
        yield selected_words
        return
    for i, word in enumerate(word_list):
        if all(len(set(word) & set(sw)) == 0 for sw in selected_words):
            yield from find_word_with_different_letters(selected_words + [word], word_list[i + 1:], N)


def find_best_word_combination(
    df_words: pd.DataFrame, 
    N: int, 
    letters: list[str], 
    positional_entropy_maps: list[dict[str, float]], 
    top_k: int = 1, 
    csv_path: Path = None
):
    """
    Find the best word combinations using position-specific letter entropy.
    
    :param df_words: DataFrame with word data
    :param N: Number of words per combination
    :param letters: List of all possible letters
    :param positional_entropy_maps: List of entropy dicts, one per position
    :param top_k: Number of top solutions to find
    :param csv_path: Optional path to CSV file for persistence
    """

    solutions = []
    start_iteration = 0
    excluded_combinations = []
    
    # Load existing solutions and initialize CSV if needed
    if csv_path:
        initialize_csv_file(csv_path)
        start_iteration, excluded_combinations = load_existing_solutions(csv_path, df_words, N)
    
    # If we already have enough solutions, just display them
    if start_iteration >= top_k:
        print(f"Already have {start_iteration} solutions, which is >= requested top-{top_k}. Nothing to do.")
        return
    
    for iteration in range(start_iteration, top_k):
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

        # Objective: maximize position-specific letter entropy with duplicate penalty
        # z[letter][pos] = 1 if letter appears at position pos in exactly one selected word
        # We want to maximize information value (entropy), penalizing duplicate letters
        max_word_length = len(positional_entropy_maps)
        
        objective_terms = []
        
        # For each letter, count how many positions it appears at
        # First occurrence gets full weight, subsequent ones get reduced weight
        for letter in letters:
            letter_positions = []
            for pos in range(max_word_length):
                if pos < len(positional_entropy_maps):
                    pos_entropy_map = positional_entropy_maps[pos]
                    if letter in pos_entropy_map:
                        letter_positions.append((pos, pos_entropy_map[letter]))
            
            # Sort by entropy (descending) to give highest weight to most informative position
            letter_positions.sort(key=lambda x: x[1], reverse=True)
            
            for idx, (pos, entropy) in enumerate(letter_positions):
                if idx == 0:
                    # First occurrence: full weight
                    weight = entropy
                else:
                    # Subsequent occurrences: reduced weight (30%)
                    # This penalizes having the same letter multiple times
                    weight = entropy * 0.3
                
                objective_terms.append(weight * z[letter][pos])
        
        solver.Maximize(sum(objective_terms))

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
            
            # Calculate information value using entropy
            total_frequency = compute_information_value(selected_words, positional_entropy_maps)
            
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
    
    # Create CSV filename with parameters (excluding top_k to allow incremental runs)
    csv_filename = f"wordle_openings_{language.value}_L{length}_N{N}.csv"
    csv_path = DATA_FOLDER_PATH / "wordle_openings" / csv_filename
    print(f"Results will be saved to: {csv_path}")
    print(f"Requested top-{top_k} solutions (will continue from existing if file exists)")

    print(f"Loading {language} words of {length} distinct letters...")

    # load words from data/words_lists/wordle_list_{language}_L{length}_base.txt
    words_file = DATA_FOLDER_PATH / "words_lists" / f"wordle_list_{language.lower()}_L{length}_base.txt"
    with open(words_file, encoding="utf-8") as f:
        words = [w.strip() for w in f if w.strip()]

    print(f"Number  words: {len(words)}")

    # Compute positional entropy maps (one per position)
    positional_entropy_maps = cmn.compute_positional_letter_entropy(words)
    
    # Also keep overall frequency for reference
    overall_frequency_map = cmn.compute_letter_frequency(words)

    # print N*L most frequent letters (overall)
    sorted_letters = sorted(overall_frequency_map.items(), key=lambda item: item[1], reverse=True)
    print(f"{N*length} most frequent letters (overall):", " ".join([item[0] for item in sorted_letters[:N*length]]))

    df_words = compute_word_entropies(words, overall_frequency_map)
    letters = list(overall_frequency_map.keys())

    find_best_word_combination(df_words, N, letters, positional_entropy_maps, top_k, csv_path)



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

if __name__ == "__main__":
    main()