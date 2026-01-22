"""
Benchmarking script for evaluate_opening_entropy function.
Tests performance with various word list sizes and opening counts.
"""

import time
from pathlib import Path

import numpy as np

from riddle import DATA_FOLDER_PATH
from wordle.main_wordle_openings_frequentist import (
    NUMBA_AVAILABLE,
    compute_cross_hints_matrix_numba_parallel,
    evaluate_opening_entropy,
    evaluate_opening_entropy_optimized,
    evaluate_opening_entropy_numba,
    evaluate_opening_entropy_numba_parallel,
)

# Clear Numba cache to avoid module path issues
numba_cache = Path(__file__).parent.parent / "src" / "wordle" / "__pycache__"
if numba_cache.exists():
    for cache_file in numba_cache.glob("*.nbi"):
        try:
            cache_file.unlink()
        except Exception:
            pass
    for cache_file in numba_cache.glob("*.nbc"):
        try:
            cache_file.unlink()
        except Exception:
            pass


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
        from wordle.main_wordle_openings_frequentist import compute_cross_hints_matrix_fast
        method = compute_cross_hints_matrix_fast
    
    hint_matrix = method(words_array)
    
    return words_list, words_array, hint_matrix


def benchmark_single_implementation(
    func,
    words_array: np.ndarray,
    hint_matrix: np.ndarray,
    opening_indices: list[int],
    n_runs: int = 3
) -> dict:
    """Benchmark a single implementation."""
    times = []
    entropy = None
    remaining = None
    
    for _ in range(n_runs):
        start = time.time()
        entropy, remaining = func(words_array, hint_matrix, opening_indices)
        elapsed = time.time() - start
        times.append(elapsed)
    
    return {
        'avg_time': np.mean(times),
        'std_time': np.std(times),
        'entropy': entropy,
        'remaining': remaining,
    }


def run_implementation_comparison():
    """Compare all implementations of evaluate_opening_entropy."""
    print("=" * 80)
    print("EVALUATE_OPENING_ENTROPY IMPLEMENTATION COMPARISON")
    print("=" * 80)
    print()
    
    # Implementations to test
    implementations = [
        ("original", evaluate_opening_entropy),
        ("optimized", evaluate_opening_entropy_optimized),
    ]
    
    if NUMBA_AVAILABLE:
        implementations.extend([
            ("numba", evaluate_opening_entropy_numba),
            ("numba_parallel", evaluate_opening_entropy_numba_parallel),
        ])
    
    # Test configurations: (n_words, n_opening_words)
    configurations = [
        (50, 2),
        (100, 2),
        (200, 3),
        (500, 4),
    ]
    
    for n_words, n_opening in configurations:
        print(f"\n{'─' * 80}")
        print(f"N={n_words} words, {n_opening} opening words")
        print(f"{'─' * 80}")
        
        # Load words and precompute hint matrix
        words_list, words_array, hint_matrix = load_words_and_hints(n_words)
        
        # Use fixed opening words (first n_opening words)
        opening_indices = list(range(n_opening))
        
        # Warm up Numba if available
        if NUMBA_AVAILABLE:
            _ = evaluate_opening_entropy_numba(words_array, hint_matrix, opening_indices)
            _ = evaluate_opening_entropy_numba_parallel(words_array, hint_matrix, opening_indices)
        
        print(f"\n{'Implementation':<20} {'Avg Time':<14} {'Speedup':<10} {'Entropy':<12} {'Remaining'}")
        print(f"{'-' * 70}")
        
        baseline_time = None
        results = {}
        
        for name, func in implementations:
            try:
                result = benchmark_single_implementation(
                    func, words_array, hint_matrix, opening_indices, n_runs=3
                )
                results[name] = result
                
                if baseline_time is None:
                    baseline_time = result['avg_time']
                
                speedup = baseline_time / result['avg_time']
                print(f"{name:<20} {result['avg_time']*1000:>8.2f} ms    "
                      f"{speedup:>6.1f}x    "
                      f"{result['entropy']:>8.2f}    "
                      f"{result['remaining']:>8.2f}")
            except Exception as e:
                print(f"{name:<20} FAILED: {e}")
        
        # Verify correctness: all implementations should give same results
        if len(results) > 1:
            ref_entropy = results.get("original", results.get("optimized", {})).get("entropy")
            ref_remaining = results.get("original", results.get("optimized", {})).get("remaining")
            all_match = True
            for name, result in results.items():
                if not np.isclose(result['entropy'], ref_entropy, rtol=1e-5):
                    print(f"  ⚠ {name} entropy mismatch: {result['entropy']} vs {ref_entropy}")
                    all_match = False
                if not np.isclose(result['remaining'], ref_remaining, rtol=1e-5):
                    print(f"  ⚠ {name} remaining mismatch: {result['remaining']} vs {ref_remaining}")
                    all_match = False
            if all_match:
                print("  ✓ All implementations produce matching results")
    
    print()
    print("=" * 80)
    print("COMPARISON COMPLETE")
    print("=" * 80)


def benchmark_with_real_words():
    """Benchmark using full real English word list with common opening combinations."""
    print("\n" + "=" * 80)
    print("BENCHMARK WITH FULL WORD LIST (FASTEST IMPLEMENTATION)")
    print("=" * 80)
    
    words_file = DATA_FOLDER_PATH / "words_lists" / "wordle_list_EN_L5_base.txt"
    
    if not words_file.exists():
        print(f"Word file not found: {words_file}")
        return
    
    with open(words_file, encoding="utf-8") as f:
        words_list = [w.strip().upper() for w in f if w.strip()]
    
    print(f"\nLoaded {len(words_list)} words from {words_file.name}")
    print("Precomputing hint matrix...")
    
    # Prepare arrays and hint matrix
    words_array = np.array(
        [list(word.encode('utf-8')) for word in words_list], 
        dtype=np.uint8
    )
    
    # Precompute hint matrix
    method = compute_cross_hints_matrix_numba_parallel if NUMBA_AVAILABLE else None
    if method is None:
        from wordle.main_wordle_openings_frequentist import compute_cross_hints_matrix_fast
        method = compute_cross_hints_matrix_fast
    
    hint_matrix = method(words_array)
    print(f"  Hint matrix size: {hint_matrix.nbytes / (1024**2):.2f} MB")
    
    # Choose fastest implementation
    if NUMBA_AVAILABLE:
        fastest_func = evaluate_opening_entropy_numba_parallel
        fastest_name = "numba_parallel"
    else:
        fastest_func = evaluate_opening_entropy_optimized
        fastest_name = "optimized"
    
    print(f"  Using: {fastest_name}")
    
    # Warm up Numba
    if NUMBA_AVAILABLE:
        _ = fastest_func(words_array, hint_matrix, [0, 1])
    
    # Benchmark with common opening words
    print(f"\nBenchmarking {fastest_name} with common openings:")
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
            entropy, remaining = fastest_func(
                words_array, hint_matrix, opening_indices
            )
            elapsed = time.time() - start
            
            print(f"   {label:<35} {elapsed*1000:>8.2f} ms   "
                  f"{entropy:>8.2f}     {remaining:>8.2f}")
        except ValueError:
            print(f"   {label:<35} Word not found in list")
    
    print()


def main():
    """Run all benchmarks."""
    print(f"\nStarting benchmark at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run implementation comparison (main benchmark)
    run_implementation_comparison()
    
    # Run real word benchmarks with fastest implementation
    try:
        benchmark_with_real_words()
    except Exception as e:
        print(f"\nReal word benchmark failed: {e}")
    
    print(f"\nBenchmark completed at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")


if __name__ == "__main__":
    main()
