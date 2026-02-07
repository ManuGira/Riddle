import numpy as np
from pathlib import Path
from riddle import DATA_FOLDER_PATH

# Try to import numba, fall back to pure Python if not available
try:
    from numba import njit, prange
    NUMBA_AVAILABLE = True
except ImportError:
    NUMBA_AVAILABLE = False
    # Create dummy decorators for when numba is not available
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args or callable(args[0]) else decorator
    def prange(n):
        return range(n)


def compute_cross_hints_matrix(words_array: np.ndarray):
    """
    Original (slower) implementation using Python loops.
    Kept for reference and testing.
    """
    N = words_array.shape[0]
    L = words_array.shape[1]

    hints_matrix = np.zeros((N, N, 2*L), dtype=np.uint8)
    for i, word_i in enumerate(words_array):
        print("Processing word", i+1, "of", N)
        for j, word_j in enumerate(words_array[i:], start=i):
            matching_letters = np.argwhere(word_i==word_j).flatten()
            for pos in matching_letters:
                letter = word_i[pos]
                hints_matrix[i, j, pos] = letter  # correct position
                hints_matrix[j, i, pos] = letter  # correct position
            common_letters = set(word_i) & set(word_j)
            for k, letter in enumerate(common_letters):
                pos = L + k
                hints_matrix[i, j, pos] = letter
                hints_matrix[j, i, pos] = letter
    print("Cross hints matrix shape:", hints_matrix.shape)
    return hints_matrix


def compute_cross_hints_matrix_optimized(words_array: np.ndarray):
    """
    Optimized version using vectorized NumPy operations.
    
    For N words of length L, computes an (N, N, 2*L) matrix where:
    - hints[i, j, :L] contains letters at matching positions (0 if no match)
    - hints[i, j, L:] contains common letters between words i and j (sorted)
    
    Uses broadcasting for position matches and bitsets for common letters.
    """
    N, L = words_array.shape
    hints_matrix = np.zeros((N, N, 2*L), dtype=np.uint8)
    
    # Part 1: Position matches - fully vectorized with broadcasting
    # words_array[:, None, :] has shape (N, 1, L)
    # words_array[None, :, :] has shape (1, N, L)
    # Comparison broadcasts to (N, N, L)
    position_matches = words_array[:, None, :] == words_array[None, :, :]
    # Where positions match, store the letter; otherwise 0
    hints_matrix[:, :, :L] = np.where(position_matches, words_array[:, None, :], 0)
    
    # Part 2: Common letters - use letter presence bitsets for efficiency
    # Create a presence matrix: (N, 256) where presence[i, c] = 1 if letter c is in word i
    presence = np.zeros((N, 256), dtype=np.uint8)
    for pos in range(L):
        presence[np.arange(N), words_array[:, pos]] = 1
    
    # Common letters between word i and word j: bitwise AND of their presence vectors
    # common_presence[i, j, c] = 1 if letter c is in both word i and word j
    common_presence = presence[:, None, :] & presence[None, :, :]  # (N, N, 256)
    
    # Extract common letters for each pair and store in hints_matrix
    # We need to iterate over pairs to pack letters into the L slots
    for i in range(N):
        for j in range(i, N):
            common_letters = np.nonzero(common_presence[i, j])[0].astype(np.uint8)
            num_common = min(len(common_letters), L)
            hints_matrix[i, j, L:L+num_common] = common_letters[:num_common]
            if i != j:
                hints_matrix[j, i, L:L+num_common] = common_letters[:num_common]
    
    return hints_matrix


def compute_cross_hints_matrix_fast(words_array: np.ndarray):
    """
    Fastest version - optimizes both position matches and common letters.
    
    Uses vectorized operations for position matches and Numba-style 
    batch processing for common letters to minimize Python loop overhead.
    """
    N, L = words_array.shape
    hints_matrix = np.zeros((N, N, 2*L), dtype=np.uint8)
    
    # Part 1: Position matches - fully vectorized
    position_matches = words_array[:, None, :] == words_array[None, :, :]
    hints_matrix[:, :, :L] = np.where(position_matches, words_array[:, None, :], 0)
    
    # Part 2: Common letters using set-based approach with batch processing
    # Pre-compute unique letters for each word as frozensets for O(1) intersection
    word_sets = [frozenset(words_array[i].tolist()) for i in range(N)]
    
    # Process in batches to reduce loop overhead
    for i in range(N):
        set_i = word_sets[i]
        for j in range(i, N):
            common = sorted(set_i & word_sets[j])
            num_common = min(len(common), L)
            if num_common > 0:
                hints_matrix[i, j, L:L+num_common] = common[:num_common]
                if i != j:
                    hints_matrix[j, i, L:L+num_common] = common[:num_common]
    
    return hints_matrix


@njit(cache=True)
def _compute_cross_hints_numba_kernel(words_array: np.ndarray, hints_matrix: np.ndarray):
    """
    Numba JIT-compiled kernel for computing cross hints matrix.
    
    This is the inner loop that gets compiled to machine code.
    """
    N = words_array.shape[0]
    L = words_array.shape[1]
    
    # Process upper triangle + diagonal
    for i in range(N):
        for j in range(i, N):
            # Part 1: Position matches
            for pos in range(L):
                if words_array[i, pos] == words_array[j, pos]:
                    hints_matrix[i, j, pos] = words_array[i, pos]
                    hints_matrix[j, i, pos] = words_array[i, pos]
            
            # Part 2: Common letters using presence array
            # Use a fixed-size array to track which letters are in word i
            presence_i = np.zeros(256, dtype=np.uint8)
            for pos in range(L):
                presence_i[words_array[i, pos]] = 1
            
            # Find common letters and store them
            common_idx = 0
            for pos in range(L):
                letter = words_array[j, pos]
                if presence_i[letter] == 1:
                    # Mark as used to avoid duplicates
                    presence_i[letter] = 0
                    hints_matrix[i, j, L + common_idx] = letter
                    hints_matrix[j, i, L + common_idx] = letter
                    common_idx += 1


def compute_cross_hints_matrix_numba(words_array: np.ndarray):
    """
    Numba-accelerated version using JIT compilation.
    
    Compiles the inner loops to machine code for maximum performance.
    First call has JIT compilation overhead, subsequent calls are fast.
    """
    N, L = words_array.shape
    hints_matrix = np.zeros((N, N, 2*L), dtype=np.uint8)
    _compute_cross_hints_numba_kernel(words_array, hints_matrix)
    return hints_matrix


@njit(parallel=True, cache=True)
def _compute_cross_hints_numba_parallel_kernel(words_array: np.ndarray, hints_matrix: np.ndarray):
    """
    Parallel Numba kernel - uses multiple CPU cores.
    
    Note: Due to symmetric updates, we process each (i,j) pair independently
    and handle symmetry within each iteration.
    """
    N = words_array.shape[0]
    L = words_array.shape[1]
    print("Starting parallel computation...")
    # Parallel over rows
    for i in prange(N):  # type: ignore[misc]
        for j in range(i, N):
            # Part 1: Position matches
            for pos in range(L):
                if words_array[i, pos] == words_array[j, pos]:
                    hints_matrix[i, j, pos] = words_array[i, pos]
                    hints_matrix[j, i, pos] = words_array[i, pos]
            
            # Part 2: Common letters
            presence_i = np.zeros(256, dtype=np.uint8)
            for pos in range(L):
                presence_i[words_array[i, pos]] = 1
            
            common_idx = 0
            for pos in range(L):
                letter = words_array[j, pos]
                if presence_i[letter] == 1:
                    presence_i[letter] = 0
                    hints_matrix[i, j, L + common_idx] = letter
                    hints_matrix[j, i, L + common_idx] = letter
                    common_idx += 1


def compute_cross_hints_matrix_numba_parallel(words_array: np.ndarray):
    """
    Parallel Numba-accelerated version using multiple CPU cores.
    
    Best for large N where parallelization overhead is worth it.
    """
    N, L = words_array.shape
    hints_matrix = np.zeros((N, N, 2*L), dtype=np.uint8)
    _compute_cross_hints_numba_parallel_kernel(words_array, hints_matrix)
    return hints_matrix

def load_words_combinations(csv_file: Path):
    """
    frequency_score, words
    5.7976,"brand, covet, funky, pails"
    5.7826,"bulky, caved, foals, print"
    5.7942,"build, caves, front, porky"
    5.7942,"built, crony, forks, paved"
    5.7942,"built, caves, frond, porky"
    5.7942,"build, covey, front, parks"
    5.7942,"built, covey, frond, parks"
    5.7704,"built, crony, folks, paved"
    5.7704,"bulky, covet, frond, pails"
    ...
    """
    import pandas as pd
    df = pd.read_csv(csv_file)
    words_combinations = []
    for _, row in df.iterrows():
        words = [w.strip().upper() for w in row['words'].split(",")]
        words_combinations.append(words)
    return words_combinations


def evaluate_opening_entropy(words_array: np.ndarray, hint_matrix: np.ndarray, opening_words_indices: list[int]):
    """
    Evaluate the expected entropy and expected remaining words
    after applying the hints from the given opening words.
    :param words_array: A numpy array of shape (N, L) with all possible words. N is number of words, L is word length.
    :param hint_matrix: A numpy array of shape (N, N, 2L) with precomputed hints between all word pairs.
    :param opening_words_indices: List of indices of the opening words in words_array. Indices are in range [0, N-1].s
    :return:
    """
    expected_entropy = 0.0
    expected_remaning_words = 0.0
    N, L = words_array.shape[0:2]

    for k in range(N):
        hint = np.zeros(2 * L, dtype=np.uint8)
        for i in opening_words_indices:
            hint_i = hint_matrix[i, k]
            # merge hints
            hint[:L] = np.max((hint[:L], hint_i[:L]), axis=0)
            matching_letters = (set(hint[L:]) | set(hint_i[L:])) - {0}
            hint[L:L+len(matching_letters)] = list(matching_letters)

        # find compatible words
        compatibles = np.argwhere(np.all(np.logical_or((hint[:L] == 0), (words_array == hint[:L])), axis=1)).flatten()
        letters_set = set(hint[L:]) - {0}
        compatibles = [carg for carg in compatibles if letters_set.issubset(set(words_array[carg]))]
        p_k = len(compatibles)/N
        expected_remaning_words += len(compatibles)
        if p_k == 0:
            raise ValueError("p_k is zero, which should not happen.")
        entropy_k = -np.log2(p_k)
        expected_entropy += entropy_k
    expected_remaning_words /= N
    expected_entropy /= N
    return expected_entropy, expected_remaning_words


def evaluate_opening_entropy_optimized(words_array: np.ndarray, hint_matrix: np.ndarray, opening_words_indices: list[int]):
    """
    Optimized version of evaluate_opening_entropy.
    
    Optimizations:
    1. Precompute letter presence bitmasks for all words (avoids repeated set() calls)
    2. Vectorize position matching across all words
    3. Use numpy operations instead of Python loops where possible
    4. Batch hint merging for all opening words
    """
    N, L = words_array.shape
    
    if len(opening_words_indices) == 0:
        # No opening words = no information, all words remain compatible
        return 0.0, float(N)
    
    # Precompute letter presence as bitmask for each word (using 32 bits for a-z)
    # letters_presence[i] is a 32-bit int where bit (letter - ord('A')) is set if letter is in word i
    letters_presence = np.zeros(N, dtype=np.uint32)
    for pos in range(L):
        # Must convert to int32 first to avoid uint8 overflow on shift
        shift_amounts = words_array[:, pos].astype(np.int32) - ord('A')
        letters_presence |= ((np.uint32(1) << shift_amounts)).astype(np.uint32)
    
    # For each target word k, merge hints from all opening words
    # and count compatible words
    total_entropy = 0.0
    total_remaining = 0
    
    # Stack hints from all opening words: shape (num_openings, N, 2L)
    opening_hints = hint_matrix[opening_words_indices, :, :]  # (num_openings, N, 2L)
    
    # Merge position hints: take max across openings for each target word
    # merged_positions[k, pos] = max over all opening words i of hint_matrix[i, k, pos]
    merged_positions = np.max(opening_hints[:, :, :L], axis=0)  # (N, L)
    
    # For common letters, we need to union across all opening words
    # Build merged letter mask for each target word
    merged_letters_mask = np.zeros(N, dtype=np.uint32)
    for i in opening_words_indices:
        for pos in range(L):
            # Get the common letters from hint_matrix[i, :, L+pos]
            letters = hint_matrix[i, :, L + pos]  # (N,) - letter at position L+pos for all targets
            # Only add non-zero letters to the mask
            nonzero_mask = letters > 0
            shift_amounts = letters[nonzero_mask].astype(np.int32) - ord('A')
            merged_letters_mask[nonzero_mask] |= ((np.uint32(1) << shift_amounts)).astype(np.uint32)
    
    # Now for each target word k, find compatible words
    for k in range(N):
        pos_hint = merged_positions[k]  # (L,) - position constraints
        letters_mask = merged_letters_mask[k]  # required letters as bitmask
        
        # Check position compatibility: for each word, all positions must match or hint is 0
        # words_array has shape (N, L), pos_hint has shape (L,)
        pos_match = (pos_hint == 0) | (words_array == pos_hint)  # (N, L)
        pos_compatible = np.all(pos_match, axis=1)  # (N,)
        
        # Check letter compatibility: required letters must be subset of word's letters
        # (letters_mask & letters_presence) == letters_mask means all required letters are present
        letters_compatible = (letters_mask & letters_presence) == letters_mask  # (N,)
        
        # Combined compatibility
        compatible_count = np.sum(pos_compatible & letters_compatible)
        
        if compatible_count == 0:
            raise ValueError(f"No compatible words for target {k}, which should not happen.")
        
        p_k = compatible_count / N
        total_remaining += compatible_count
        total_entropy += -np.log2(p_k)
    
    return total_entropy / N, total_remaining / N


@njit(cache=True)
def _evaluate_opening_entropy_numba_kernel(
    words_array: np.ndarray,
    hint_matrix: np.ndarray,
    opening_indices: np.ndarray,
    letters_presence: np.ndarray
) -> tuple[float, float]:
    """
    Numba JIT-compiled kernel for evaluate_opening_entropy.
    """
    N = words_array.shape[0]
    L = words_array.shape[1]
    num_openings = len(opening_indices)
    
    total_entropy = 0.0
    total_remaining = 0.0
    
    for k in range(N):
        # Merge position hints from all opening words
        pos_hint = np.zeros(L, dtype=np.uint8)
        letters_mask = np.uint32(0)
        
        for oi in range(num_openings):
            i = opening_indices[oi]
            # Merge position hints (take max)
            for pos in range(L):
                if hint_matrix[i, k, pos] > pos_hint[pos]:
                    pos_hint[pos] = hint_matrix[i, k, pos]
            # Merge common letters into bitmask
            for pos in range(L):
                letter = hint_matrix[i, k, L + pos]
                if letter > 0:
                    letters_mask |= np.uint32(1) << np.uint32(letter - 65)  # ord('A') = 65
        
        # Count compatible words
        compatible_count = 0
        for w in range(N):
            # Check position compatibility
            pos_ok = True
            for pos in range(L):
                if pos_hint[pos] != 0 and words_array[w, pos] != pos_hint[pos]:
                    pos_ok = False
                    break
            
            if pos_ok:
                # Check letter compatibility
                if (letters_mask & letters_presence[w]) == letters_mask:
                    compatible_count += 1
        
        p_k = compatible_count / N
        total_remaining += compatible_count
        total_entropy += -np.log2(p_k)
    
    return total_entropy / N, total_remaining / N


def evaluate_opening_entropy_numba(words_array: np.ndarray, hint_matrix: np.ndarray, opening_words_indices: list[int]):
    """
    Numba-accelerated version of evaluate_opening_entropy.
    
    Uses JIT compilation for the inner loops.
    """
    N, L = words_array.shape
    
    if len(opening_words_indices) == 0:
        return 0.0, float(N)
    
    # Precompute letter presence bitmask for each word
    # Must convert to int32 first to avoid uint8 overflow on shift
    letters_presence = np.zeros(N, dtype=np.uint32)
    for pos in range(L):
        shift_amounts = words_array[:, pos].astype(np.int32) - ord('A')
        letters_presence |= ((np.uint32(1) << shift_amounts)).astype(np.uint32)
    
    opening_indices = np.array(opening_words_indices, dtype=np.int64)
    
    return _evaluate_opening_entropy_numba_kernel(
        words_array, hint_matrix, opening_indices, letters_presence
    )


@njit(parallel=True, cache=True)
def _evaluate_opening_entropy_numba_parallel_kernel(
    words_array: np.ndarray,
    hint_matrix: np.ndarray,
    opening_indices: np.ndarray,
    letters_presence: np.ndarray,
    results: np.ndarray  # (N, 2) array to store entropy and count per target
):
    """
    Parallel Numba kernel for evaluate_opening_entropy.
    """
    N = words_array.shape[0]
    L = words_array.shape[1]
    num_openings = len(opening_indices)
    
    for k in prange(N):  # type: ignore[misc]
        # Merge position hints from all opening words
        pos_hint = np.zeros(L, dtype=np.uint8)
        letters_mask = np.uint32(0)
        
        for oi in range(num_openings):
            i = opening_indices[oi]
            for pos in range(L):
                if hint_matrix[i, k, pos] > pos_hint[pos]:
                    pos_hint[pos] = hint_matrix[i, k, pos]
            for pos in range(L):
                letter = hint_matrix[i, k, L + pos]
                if letter > 0:
                    letters_mask |= np.uint32(1) << np.uint32(letter - 65)
        
        # Count compatible words
        compatible_count = 0
        for w in range(N):
            pos_ok = True
            for pos in range(L):
                if pos_hint[pos] != 0 and words_array[w, pos] != pos_hint[pos]:
                    pos_ok = False
                    break
            
            if pos_ok:
                if (letters_mask & letters_presence[w]) == letters_mask:
                    compatible_count += 1
        
        p_k = compatible_count / N
        results[k, 0] = -np.log2(p_k)
        results[k, 1] = compatible_count


def evaluate_opening_entropy_numba_parallel(words_array: np.ndarray, hint_matrix: np.ndarray, opening_words_indices: list[int]):
    """
    Parallel Numba-accelerated version of evaluate_opening_entropy.
    
    Uses multiple CPU cores for maximum performance.
    """
    N, L = words_array.shape
    
    if len(opening_words_indices) == 0:
        return 0.0, float(N)
    
    # Precompute letter presence bitmask for each word
    # Must convert to int32 first to avoid uint8 overflow on shift
    letters_presence = np.zeros(N, dtype=np.uint32)
    for pos in range(L):
        shift_amounts = words_array[:, pos].astype(np.int32) - ord('A')
        letters_presence |= ((np.uint32(1) << shift_amounts)).astype(np.uint32)
    
    opening_indices = np.array(opening_words_indices, dtype=np.int64)
    results = np.zeros((N, 2), dtype=np.float64)
    
    _evaluate_opening_entropy_numba_parallel_kernel(
        words_array, hint_matrix, opening_indices, letters_presence, results
    )
    
    total_entropy = np.sum(results[:, 0])
    total_remaining = np.sum(results[:, 1])
    
    return total_entropy / N, total_remaining / N


def compute_word_raw_entropy(words_list: str, entropy_maps):
    # sum the entropies for each letter in the word
    # if a letter appears multiple times, keep the highest entropy only

    # Todo: aggregate rows of hint matrix would be more accurate

    long_word = "".join(words_list)
    L = len(entropy_maps)
    entropies_to_sum: dict[str, float] = {letter: 0 for letter in set(long_word)}
    for pos, letter in enumerate(long_word):
        entropy = entropy_maps[pos%L][letter]
        entropies_to_sum[letter] = max(entropies_to_sum[letter], entropy)
    return sum(entropies_to_sum.values())


def compute_word_match_with_hints_matrix(words_list: list[str]):
    words_list = [w.upper() for w in words_list]
    # convert words_list to numpy array of shape (N, L) and dtype uint8
    words_array = np.array([list(word.encode('utf-8')) for word in words_list], dtype=np.uint8)
    hint_matrix = compute_cross_hints_matrix_numba_parallel(words_array)

    print("Words array shape:", words_array.shape)

    if False:
        opening_candidates_file = DATA_FOLDER_PATH / "wordle_openings" / "wordle_openings_EN_L5_N3.csv"
        opening_list = load_words_combinations(opening_candidates_file)
        opening_list = [
                           ["HATES", "ROUND", "CLIMB"],
                           # ["BLANK", "BLANK", "BLANK", "BLANK"],
                           # ["BLANK", "CREST", "BLANK", "BLANK"],
                           # ["BLANK", "CREST", "WIMPY", "BLANK"],
                           # ["BLANK", "CREST", "WIMPY", "DOUGH"],
                       ] + opening_list
    else:
        # make all combinations of 2 words from words_list (order does not matter)
        from riddle.common import compute_positional_letter_entropy
        entropy_maps = compute_positional_letter_entropy(words_list)
        # compute entropy score for each word
        word_entropy_scores = [(word, compute_word_raw_entropy(word, entropy_maps)) for word in words_list]
        # sort by entropy score descending
        word_entropy_scores.sort(key=lambda x: x[1], reverse=True)
        sorted_word_list = [wes[0] for wes in word_entropy_scores]
        best_raw_entropy = word_entropy_scores[0][1]
        print("Top 10 words by positional letter entropy:")
        for w, s in word_entropy_scores[:10]:
            print(f"{w}: {s:.4f}")

        # generate combinations of 2 words using a zig-zag pattern from the sorted list
        from itertools import combinations
        opening_list = []
        N = len(sorted_word_list)

        for i in range(N):
            for j in range(i):
                opening_list.append([sorted_word_list[i], sorted_word_list[j]])
        print(f"Generated {len(opening_list)} opening combinations of 2 words.")


    # expected_entropies: list[tuple[float, list[str]]] = []
    best_entropy = -1.0
    best_opening = []

    raw_entropy_threshold = best_raw_entropy * 2 ** (1 / len(opening_list[0])) * 1.1
    k = 0
    for i, opening in enumerate(opening_list):
        # if the entropy of the tuple is low, skip it
        raw_entropy = compute_word_raw_entropy("".join(opening), entropy_maps)

        if raw_entropy < raw_entropy_threshold:
            k += 1
            continue

        opening_words_indices = [words_list.index(w) for w in opening]

        expected_entropy, expected_remaning_words = evaluate_opening_entropy_numba_parallel(words_array, hint_matrix,
                                                                             opening_words_indices)
        # expected_entropies.append((expected_entropy, opening))
        if expected_entropy > best_entropy:
            best_entropy = expected_entropy
            best_opening = opening
            print(f"({k}/{i}/{len(opening_list)})Opening: {'-'.join(opening)}, Avg remaining words: {expected_remaning_words:.2f}, entropy: {expected_entropy:.2f}")

    return


def main():
    # words = ["apple", "brave", "crane", "doubt", "eagle", "flint", "grape", "honey", "input", "jumpy"]




    # load words from data/words_lists/wordle_list_{language}_L{length}_base.txt
    words_file = DATA_FOLDER_PATH / "words_lists" / "wordle_list_EN_L5_base.txt"
    with open(words_file, encoding="utf-8") as f:
        words = [w.strip() for w in f if w.strip()]
    compute_word_match_with_hints_matrix(words)

if __name__ == "__main__":
    main()