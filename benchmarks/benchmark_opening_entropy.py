"""
Benchmarking script for evaluate_opening_entropy function.
Tests performance with various word list sizes and opening counts.
"""

import time
from pathlib import Path

import numpy as np

# Clear Numba cache to avoid module path issues
numba_cache = Path(__file__).parent.parent / "src" / "wordle" / "__pycache__"
if numba_cache.exists():
    for cache_file in numba_cache.glob("*.nbi"):
        try:
            cache_file.unlink()
        except:
            pass
    for cache_file in numba_cache.glob("*.nbc"):
        try:
            cache_file.unlink()
        except:
            pass

from riddle import DATA_FOLDER_PATH
from wordle.wordle_openings_2 import (
    NUMBA_AVAILABLE, compute_cross_hints_matrix_numba_parallel,
    evaluate_opening_entropy)


def load_words_and_hints(n_words: int) -> tuple[list[str], np.ndarray, np.ndarray]:
    """
    Load n_words from the English word list and precompute hint matrix.
    Returns words_list, words_array, and hint_matrix.
    """
    words_file = DATA_FOLDER_PATH / "words_lists" / "wordle_list_EN_L5_base.txt"
    with open(words_file, encoding="utf-8") as f:
        words_list = [w.strip().upper() for w in f if w.strip()][:n_words]
    
    words_array = np.array(
        [list(word.encode('utf-8')) for word in words_list], 
        dtype=np.uint8
    )
    
    # Precompute hint matrix (using fastest method available)
    method = compute_cross_hints_matrix_numba_parallel if NUMBA_AVAILABLE else None
    if method is None:
        from wordle.wordle_openings_2 import compute_cross_hints_matrix_fast
        method = compute_cross_hints_matrix_fast
    
    hint_matrix = method(words_array)
    
    return words_list, words_array, hint_matrix


def benchmark_evaluate_opening_entropy(
    words_array: np.ndarray,
    hint_matrix: np.ndarray,
    n_opening_words: int,
    n_runs: int = 5
) -> dict:
    """
    Benchmark evaluate_opening_entropy with different numbers of opening words.
    
    Args:
        words_array: Array of words
        hint_matrix: Precomputed hint matrix
        n_opening_words: Number of opening words to test
        n_runs: Number of runs for averaging
    
    Returns:
        Dictionary with timing statistics
    """
    N = words_array.shape[0]
    np.random.seed(42)
    
    timings = []
    
    for run in range(n_runs):
        # Select random opening words
        opening_indices = np.random.choice(N, n_opening_words, replace=False).tolist()
        
        start = time.time()
        entropy, remaining = evaluate_opening_entropy(
            words_array, hint_matrix, opening_indices
        )
        elapsed = time.time() - start
        
        timings.append({
            'run': run + 1,
            'time': elapsed,
            'entropy': entropy,
            'remaining': remaining,
        })
    
    times = [t['time'] for t in timings]
    return {
        'n_words': N,
        'n_opening_words': n_opening_words,
        'n_runs': n_runs,
        'avg_time': np.mean(times),
        'std_time': np.std(times),
        'min_time': np.min(times),
        'max_time': np.max(times),
        'avg_entropy': np.mean([t['entropy'] for t in timings]),
        'avg_remaining': np.mean([t['remaining'] for t in timings]),
        'timings': timings,
    }


def run_comprehensive_benchmark():
    """Run comprehensive benchmarks with different word list sizes."""
    print("=" * 80)
    print("EVALUATE_OPENING_ENTROPY BENCHMARK")
    print("=" * 80)
    print()
    
    # Test configurations: (n_words, opening_words_list)
    configurations = [
        (50, [1, 2, 3, 4]),
        (100, [1, 2, 3, 4]),
        (200, [1, 2, 4]),
        (500, [1, 2, 4]),
    ]
    
    all_results = []
    
    for n_words, opening_counts in configurations:
        print(f"\n{'─' * 80}")
        print(f"Testing with {n_words} words")
        print(f"{'─' * 80}")
        
        # Load words and precompute hint matrix
        print(f"Loading {n_words} words and precomputing hint matrix...")
        words_list, words_array, hint_matrix = load_words_and_hints(n_words)
        print(f"  Words shape: {words_array.shape}, Hint matrix shape: {hint_matrix.shape}")
        
        # Benchmark evaluate_opening_entropy
        print(f"\nBenchmarking evaluate_opening_entropy:")
        print(f"   {'Opening Words':<15} {'Avg Time':<12} {'Std':<10} {'Avg Entropy':<12} {'Avg Remaining'}")
        print(f"   {'-' * 70}")
        
        for n_opening in opening_counts:
            if n_opening >= n_words:
                continue
            
            results = benchmark_evaluate_opening_entropy(
                words_array, hint_matrix, n_opening, n_runs=5
            )
            
            print(f"   {n_opening:<15} "
                  f"{results['avg_time']*1000:>8.2f} ms   "
                  f"{results['std_time']*1000:>6.2f} ms  "
                  f"{results['avg_entropy']:>8.2f}     "
                  f"{results['avg_remaining']:>8.2f}")
            
            all_results.append(results)
    
    print()
    print("=" * 80)
    print("BENCHMARK COMPLETE")
    print("=" * 80)
    
    return all_results


def benchmark_with_real_words():
    """Benchmark using full real English word list with common opening combinations."""
    print("\n" + "=" * 80)
    print("BENCHMARK WITH FULL WORD LIST")
    print("=" * 80)
    
    words_file = DATA_FOLDER_PATH / "words_lists" / "wordle_list_EN_L5_base.txt"
    
    if not words_file.exists():
        print(f"Word file not found: {words_file}")
        return
    
    with open(words_file, encoding="utf-8") as f:
        words_list = [w.strip().upper() for w in f if w.strip()]
    
    print(f"\nLoaded {len(words_list)} words from {words_file.name}")
    print(f"Precomputing hint matrix...")
    
    # Prepare arrays and hint matrix
    words_array = np.array(
        [list(word.encode('utf-8')) for word in words_list], 
        dtype=np.uint8
    )
    
    # Precompute hint matrix (not benchmarked here)
    method = compute_cross_hints_matrix_numba_parallel if NUMBA_AVAILABLE else None
    if method is None:
        from wordle.wordle_openings_2 import compute_cross_hints_matrix_fast
        method = compute_cross_hints_matrix_fast
    
    hint_matrix = method(words_array)
    print(f"  Hint matrix size: {hint_matrix.nbytes / (1024**2):.2f} MB")
    
    # Benchmark with common opening words
    print(f"\nBenchmarking evaluate_opening_entropy with common openings:")
    common_openings = [
        (["CRANE"], "Single: CRANE"),
        (["SLATE"], "Single: SLATE"),
        (["CRANE", "STYLE"], "Double: CRANE-STYLE"),
        (["SLATE", "CROWN"], "Double: SLATE-CROWN"),
        (["CRANE", "STYLE", "BINGO"], "Triple: CRANE-STYLE-BINGO"),
    ]
    
    print(f"   {'Opening':<35} {'Time':<12} {'Entropy':<12} {'Remaining'}")
    print(f"   {'-' * 70}")
    
    for opening_words, label in common_openings:
        try:
            opening_indices = [words_list.index(w.upper()) for w in opening_words]
            
            start = time.time()
            entropy, remaining = evaluate_opening_entropy(
                words_array, hint_matrix, opening_indices
            )
            elapsed = time.time() - start
            
            print(f"   {label:<35} {elapsed*1000:>8.2f} ms   "
                  f"{entropy:>8.2f}     {remaining:>8.2f}")
        except ValueError as e:
            print(f"   {label:<35} Word not found in list")
    
    print()


def main():
    """Run all benchmarks."""
    print(f"\nStarting benchmark at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run synthetic benchmarks
    run_comprehensive_benchmark()
    
    # Run real word benchmarks
    try:
        benchmark_with_real_words()
    except Exception as e:
        print(f"\nReal word benchmark failed: {e}")
    
    print(f"\nBenchmark completed at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")


if __name__ == "__main__":
    main()
