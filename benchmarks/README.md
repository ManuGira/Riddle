# Benchmarks

This folder contains performance benchmarking scripts for the Riddle project.

## Important Notes

- **Numba Cache**: The benchmarks automatically clear Numba's JIT cache to avoid module path issues when running from different locations.
- **First Run**: The first run with Numba may be slower due to JIT compilation. Subsequent runs will be faster.
- If you see Numba-related errors, try deleting `src/wordle/__pycache__/*.nbi` and `*.nbc` files manually.

## Wordle Benchmarks

### Cross Hints Matrix Generation

**Function benchmarked:** `compute_cross_hints_matrix_*`

Benchmark different implementations of the cross hints matrix computation:

```bash
uv run benchmarks/benchmark_cross_hints_matrix.py
```

This benchmarks:
- `compute_cross_hints_matrix` - Original Python loop implementation
- `compute_cross_hints_matrix_optimized` - Optimized NumPy vectorized version  
- `compute_cross_hints_matrix_fast` - Fast implementation with set operations
- `compute_cross_hints_matrix_numba` - Numba JIT-compiled version
- `compute_cross_hints_matrix_numba_parallel` - Numba parallel version

### Opening Entropy Evaluation

**Function benchmarked:** `evaluate_opening_entropy`

Benchmark the opening word evaluation for Wordle (hint matrix is precomputed, not benchmarked):

```bash
uv run benchmarks/benchmark_opening_entropy.py
```

This benchmarks:
- Performance of `evaluate_opening_entropy` with different word list sizes (50, 100, 200, 500 words)
- Performance with different numbers of opening words (1-4)
- Real English word list benchmarks (3,500+ words)
- Common opening word combinations (CRANE, SLATE, etc.)

**Note:** The hint matrix is precomputed before each benchmark run and is not included in timing measurements.

## Running All Benchmarks

To run all wordle benchmarks:

```bash
uv run benchmarks/benchmark_wordle_all.py
```
