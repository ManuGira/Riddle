# Cross Hints Matrix Implementations

This document explains the three implementations of `compute_cross_hints_matrix` in `src/wordle/wordle_openings_2.py`.

## Overview

The cross hints matrix is an `(N, N, 2*L)` tensor where:
- `N` = number of words
- `L` = word length
- `hints[i, j, :L]` = letters at matching positions between words i and j (0 if no match)
- `hints[i, j, L:]` = common letters between words i and j (sorted, up to L unique letters)

## Implementations

### 1. `compute_cross_hints_matrix` (Original)

**Strategy:** Nested Python loops with per-element operations.

```python
for i, word_i in enumerate(words_array):
    for j, word_j in enumerate(words_array[i:], start=i):
        # Find matching positions
        matching_letters = np.argwhere(word_i == word_j).flatten()
        for pos in matching_letters:
            hints_matrix[i, j, pos] = word_i[pos]
        # Find common letters
        common_letters = set(word_i) & set(word_j)
        for k, letter in enumerate(common_letters):
            hints_matrix[i, j, L + k] = letter
```

**Characteristics:**
- Easy to understand and debug
- O(N²) loop iterations in Python
- Creates new sets for each word pair
- Suitable for small datasets or reference implementation

**Performance:** Baseline (1x)

---

### 2. `compute_cross_hints_matrix_optimized` (Optimized)

**Strategy:** Vectorized position matching + precomputed presence bitsets.

```python
# Part 1: Fully vectorized position matching
position_matches = words_array[:, None, :] == words_array[None, :, :]
hints_matrix[:, :, :L] = np.where(position_matches, words_array[:, None, :], 0)

# Part 2: Precompute letter presence as (N, 256) bitset
presence = np.zeros((N, 256), dtype=np.uint8)
for pos in range(L):
    presence[np.arange(N), words_array[:, pos]] = 1

# Compute common letters via bitwise AND
common_presence = presence[:, None, :] & presence[None, :, :]  # (N, N, 256)
```

**Characteristics:**
- Position matching is fully vectorized (no Python loops)
- Uses broadcasting: `(N, 1, L)` vs `(1, N, L)` → `(N, N, L)`
- Precomputes presence matrix to avoid repeated set creation
- Still requires Python loop to pack common letters into output

**Performance:** ~3-4x faster than original

---

### 3. `compute_cross_hints_matrix_fast` (Fastest)

**Strategy:** Vectorized position matching + precomputed frozensets.

```python
# Part 1: Same vectorized position matching
position_matches = words_array[:, None, :] == words_array[None, :, :]
hints_matrix[:, :, :L] = np.where(position_matches, words_array[:, None, :], 0)

# Part 2: Precompute frozensets for O(1) intersection
word_sets = [frozenset(words_array[i].tolist()) for i in range(N)]

for i in range(N):
    set_i = word_sets[i]
    for j in range(i, N):
        common = sorted(set_i & word_sets[j])
        hints_matrix[i, j, L:L+len(common)] = common[:L]
```

**Characteristics:**
- Same vectorized position matching as optimized version
- Precomputes frozensets once (N operations) instead of per-pair (N² operations)
- `frozenset` intersection is O(min(|A|, |B|)) = O(L)
- Avoids the large (N, N, 256) intermediate array

**Performance:** ~11-14x faster than original

---

### 4. `compute_cross_hints_matrix_numba` (Numba JIT)

**Strategy:** JIT-compiled inner loops using Numba.

```python
@njit(cache=True)
def _compute_cross_hints_numba_kernel(words_array, hints_matrix):
    N, L = words_array.shape[0], words_array.shape[1]
    for i in range(N):
        for j in range(i, N):
            # Position matches
            for pos in range(L):
                if words_array[i, pos] == words_array[j, pos]:
                    hints_matrix[i, j, pos] = words_array[i, pos]
                    hints_matrix[j, i, pos] = words_array[i, pos]
            
            # Common letters with presence array
            presence_i = np.zeros(256, dtype=np.uint8)
            for pos in range(L):
                presence_i[words_array[i, pos]] = 1
            # ...
```

**Characteristics:**
- Compiles Python loops to machine code
- First call has ~0.5s JIT compilation overhead (cached thereafter)
- Uses `cache=True` to persist compiled code to disk
- Simple loops work best with Numba

**Performance:** ~150-250x faster than original

---

### 5. `compute_cross_hints_matrix_numba_parallel` (Parallel Numba)

**Strategy:** Same as Numba, but parallelized across CPU cores.

```python
@njit(parallel=True, cache=True)
def _compute_cross_hints_numba_parallel_kernel(words_array, hints_matrix):
    N, L = words_array.shape[0], words_array.shape[1]
    for i in prange(N):  # prange enables parallelization
        for j in range(i, N):
            # Same logic as single-threaded version
```

**Characteristics:**
- Uses `prange` for automatic parallelization over rows
- Scales with available CPU cores
- Best for large N where parallelization overhead is worth it
- Thread-safe due to non-overlapping symmetric writes

**Performance:** ~400-860x faster than original

---

## Performance Comparison

Benchmarks on random 5-letter words:

| Words (N) | Original | Optimized | Fast | Numba | Numba Parallel |
|-----------|----------|-----------|------|-------|----------------|
| 50 | 0.047s | 3.1x | 11.8x | **147x** | **383x** |
| 100 | 0.150s | 6.4x | 17.7x | **245x** | **863x** |
| 500 | ~3.5s | 0.56s | 0.18s | **0.014s** | **0.002s** |

**Key findings:**
- Numba parallel achieves **100-800x speedup** over the original Python implementation
- For 500 words, Numba parallel takes only 2ms compared to ~3.5 seconds for the original
- The parallelization scales well with multiple CPU cores

---

## When to Use Each

| Implementation | Use Case |
|----------------|----------|
| `compute_cross_hints_matrix` | Debugging, reference, very small N |
| `compute_cross_hints_matrix_optimized` | When you need the presence matrix for other operations |
| `compute_cross_hints_matrix_fast` | When numba is not available |
| `compute_cross_hints_matrix_numba` | Single-threaded production use |
| `compute_cross_hints_matrix_numba_parallel` | **Best choice** - multi-core production use |

---

## Memory Usage

| Implementation | Peak Memory |
|----------------|-------------|
| Original | O(N² × L) for output only |
| Optimized | O(N² × 256) for presence matrix |
| Fast | O(N × L) for frozensets + O(N² × L) for output |

The fast version has the best memory profile for large N, as it avoids the 256-wide presence matrix.

## Numba Installation

Numba is optional but highly recommended. Install with:

```bash
uv add numba
```

If numba is not installed, the code falls back to the `fast` implementation automatically.
