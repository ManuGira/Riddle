"""
Run all Wordle-related benchmarks.
"""

import time

from benchmark_cross_hints_matrix import run_benchmark_suite as run_cross_hints_benchmark
from benchmark_opening_entropy import run_comprehensive_benchmark, benchmark_with_real_words


def main():
    """Run all wordle benchmarks."""
    print(f"\n{'=' * 80}")
    print(f"WORDLE BENCHMARKS - COMPREHENSIVE SUITE")
    print(f"Started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 80}\n")
    
    # Part 1: Cross Hints Matrix Generation
    print("\n" + "█" * 80)
    print("PART 1: CROSS HINTS MATRIX GENERATION")
    print("█" * 80 + "\n")
    run_cross_hints_benchmark()
    
    # Part 2: Opening Entropy Evaluation (Synthetic)
    print("\n" + "█" * 80)
    print("PART 2: OPENING ENTROPY EVALUATION (SYNTHETIC DATA)")
    print("█" * 80 + "\n")
    run_comprehensive_benchmark()
    
    # Part 3: Opening Entropy Evaluation (Real Words)
    print("\n" + "█" * 80)
    print("PART 3: OPENING ENTROPY EVALUATION (REAL ENGLISH WORDS)")
    print("█" * 80 + "\n")
    try:
        benchmark_with_real_words()
    except Exception as e:
        print(f"\nReal word benchmark failed: {e}")
    
    print(f"\n{'=' * 80}")
    print(f"ALL BENCHMARKS COMPLETE")
    print(f"Completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    main()
