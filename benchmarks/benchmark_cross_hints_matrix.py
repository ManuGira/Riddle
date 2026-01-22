"""
Benchmark script for cross hints matrix computation methods.
Compares performance of different implementations.
"""

import time
import numpy as np
from pathlib import Path

from riddle import DATA_FOLDER_PATH
from wordle.main_wordle_openings_frequentist import (
    compute_cross_hints_matrix,
    compute_cross_hints_matrix_optimized,
    compute_cross_hints_matrix_fast,
    compute_cross_hints_matrix_numba,
    compute_cross_hints_matrix_numba_parallel,
    NUMBA_AVAILABLE,
)

# Add src to path for imports
# src_path = Path(__file__).parent.parent / "src"
# sys.path.insert(0, str(src_path))

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


def load_words_array_from_file(n_words: int) -> np.ndarray:
    """Load n_words from the English word list as a numpy array."""
    words_file = DATA_FOLDER_PATH / "words_lists" / "wordle_list_EN_L5_base.txt"
    with open(words_file, encoding="utf-8") as f:
        words = [w.strip().upper() for w in f if w.strip()][:n_words]
    return np.array([list(word.encode('utf-8')) for word in words], dtype=np.uint8)


def benchmark_implementation(func, words_array: np.ndarray, name: str, warm_up: bool = False):
    """Benchmark a single implementation."""
    if warm_up:
        # Warm up for JIT compilation
        _ = func(words_array[:5])
    
    start = time.perf_counter()
    result = func(words_array)
    elapsed = time.perf_counter() - start
    
    return result, elapsed


def verify_correctness(reference, result, name: str, L: int, N: int):
    """Verify that result matches reference implementation."""
    # Position matches should be identical
    try:
        np.testing.assert_array_equal(reference[:, :, :L], result[:, :, :L])
    except AssertionError:
        print(f"  ⚠ {name}: Position matches differ from reference!")
        return False
    
    # Common letters sets should match (order may differ)
    for i in range(min(N, 10)):
        for j in range(min(N, 10)):
            ref_common = set(reference[i, j, L:]) - {0}
            result_common = set(result[i, j, L:]) - {0}
            if ref_common != result_common:
                print(f"  ⚠ {name}: Common letters mismatch at ({i},{j})")
                return False
    
    return True


def run_benchmark_suite():
    """Run comprehensive benchmark suite."""
    print("=" * 80)
    print("CROSS HINTS MATRIX BENCHMARK")
    print("=" * 80)
    print()
    
    # Test configurations
    test_sizes = [50, 100, 200, 500, 1000]
    
    for n_words in test_sizes:
        print(f"{'─' * 80}")
        print(f"Benchmarking with {n_words} words (5 letters each)")
        print(f"{'─' * 80}")
        
        words_array = load_words_array_from_file(n_words)
        L = 5
        
        results = {}
        
        # Benchmark original (skip for large N)
        if n_words <= 100:
            print("  Original implementation...")
            result, elapsed = benchmark_implementation(
                compute_cross_hints_matrix, words_array, "original"
            )
            results["original"] = (result, elapsed)
            print(f"    Time: {elapsed:.4f}s")
            reference = result
        else:
            print(f"  Original implementation: SKIPPED (too slow for N={n_words})")
            reference = None
        
        # Benchmark optimized
        print("  Optimized implementation...")
        result, elapsed = benchmark_implementation(
            compute_cross_hints_matrix_optimized, words_array, "optimized"
        )
        results["optimized"] = (result, elapsed)
        print(f"    Time: {elapsed:.4f}s")
        if reference is None:
            reference = result
        
        # Benchmark fast
        print("  Fast implementation...")
        result, elapsed = benchmark_implementation(
            compute_cross_hints_matrix_fast, words_array, "fast"
        )
        results["fast"] = (result, elapsed)
        print(f"    Time: {elapsed:.4f}s")
        
        # Benchmark numba if available
        if NUMBA_AVAILABLE:
            print("  Numba implementation...")
            try:
                result, elapsed = benchmark_implementation(
                    compute_cross_hints_matrix_numba, words_array, "numba", warm_up=True
                )
                results["numba"] = (result, elapsed)
                print(f"    Time: {elapsed:.4f}s")
            except Exception as e:
                print(f"    FAILED: {e}")
            
            print("  Numba parallel implementation...")
            try:
                result, elapsed = benchmark_implementation(
                    compute_cross_hints_matrix_numba_parallel, words_array, "numba_parallel", warm_up=True
                )
                results["numba_parallel"] = (result, elapsed)
                print(f"    Time: {elapsed:.4f}s")
            except Exception as e:
                print(f"    FAILED: {e}")
        else:
            print("  Numba implementations: NOT AVAILABLE (install numba for better performance)")
        
        # Verify correctness
        print("\n  Correctness verification:")
        all_correct = True
        for name, (result, _) in results.items():
            if name == "original" and n_words <= 100:
                continue  # Skip verifying original against itself
            correct = verify_correctness(reference, result, name, L, n_words)
            if correct:
                print(f"    ✓ {name}")
            else:
                all_correct = False
        
        if not all_correct:
            print("  ⚠ WARNING: Some implementations produced different results!")
        
        # Performance comparison
        print("\n  Performance comparison:")
        baseline_time = results.get("original", results.get("optimized", results["fast"]))[1]
        
        for name, (_, elapsed) in sorted(results.items(), key=lambda x: x[1][1]):
            speedup = baseline_time / elapsed
            print(f"    {name:20s}: {elapsed:7.4f}s  ({speedup:5.1f}x speedup)")
        
        print()
    
    print("=" * 80)
    print("BENCHMARK COMPLETE")
    print("=" * 80)


def main():
    """Main entry point."""
    print(f"\nStarting benchmark at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    run_benchmark_suite()
    print(f"\nBenchmark completed at {time.strftime('%Y-%m-%d %H:%M:%S')}\n")


if __name__ == "__main__":
    main()
