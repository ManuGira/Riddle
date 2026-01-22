"""
Unit tests for wordle_openings_2 module.
"""
import numpy as np
import pytest

from wordle.wordle_openings_2 import (
    compute_cross_hints_matrix,
    compute_cross_hints_matrix_optimized,
    compute_cross_hints_matrix_fast,
    compute_cross_hints_matrix_numba,
    compute_cross_hints_matrix_numba_parallel,
    NUMBA_AVAILABLE,
)


def words_to_array(words: list[str]) -> np.ndarray:
    """Helper to convert word list to numpy uint8 array."""
    words_upper = [w.upper() for w in words]
    return np.array([list(word.encode('utf-8')) for word in words_upper], dtype=np.uint8)


class TestComputeCrossHintsMatrix:
    """Tests for compute_cross_hints_matrix function."""
    
    def test_basic_shape(self):
        """Test that output has correct shape (N, N, 2*L)."""
        words = ["apple", "brave", "crane"]
        words_array = words_to_array(words)
        
        result = compute_cross_hints_matrix(words_array)
        
        N = len(words)
        L = len(words[0])
        assert result.shape == (N, N, 2 * L)
        assert result.dtype == np.uint8
    
    def test_identical_words(self):
        """Test with same word - should have all positions matching."""
        words = ["hello", "hello"]
        words_array = words_to_array(words)
        
        result = compute_cross_hints_matrix(words_array)
        
        # For identical words, first L positions should contain the word itself
        expected_letters = np.array(list("HELLO".encode('utf-8')), dtype=np.uint8)
        np.testing.assert_array_equal(result[0, 1, :5], expected_letters)
        np.testing.assert_array_equal(result[1, 0, :5], expected_letters)
        
        # Common letters should be in positions L to 2L (unique letters: H, E, L, O)
        common_letters_section = result[0, 1, 5:10]
        assert set(common_letters_section) - {0} == set(expected_letters)
    
    def test_no_common_letters(self):
        """Test with words sharing no letters."""
        words = ["abcde", "fghij"]
        words_array = words_to_array(words)
        
        result = compute_cross_hints_matrix(words_array)
        
        # No matching positions
        assert np.all(result[0, 1, :5] == 0)
        assert np.all(result[1, 0, :5] == 0)
        
        # No common letters
        assert np.all(result[0, 1, 5:] == 0)
        assert np.all(result[1, 0, 5:] == 0)
    
    def test_one_matching_position(self):
        """Test words with one letter at same position."""
        words = ["apple", "ample"]  # 'a' at pos 0, 'p' at pos 1, 'l' at pos 3, 'e' at pos 4
        words_array = words_to_array(words)
        
        result = compute_cross_hints_matrix(words_array)
        
        # Check matching positions (both have same letters at 0, 3, 4)
        a_code = ord('A')
        p_code = ord('P')
        l_code = ord('L')
        e_code = ord('E')
        
        # Position 0: both have 'A'
        assert result[0, 1, 0] == a_code
        # Position 3: both have 'L'
        assert result[0, 1, 3] == l_code
        # Position 4: both have 'E'
        assert result[0, 1, 4] == e_code
        
        # Position 1: 'P' vs 'M' - no match
        assert result[0, 1, 1] == 0
        # Position 2: 'P' vs 'P' - match!
        assert result[0, 1, 2] == p_code
    
    def test_common_letters_different_positions(self):
        """Test words with common letters at different positions."""
        words = ["abcde", "edcba"]  # Same letters, reversed
        words_array = words_to_array(words)
        
        result = compute_cross_hints_matrix(words_array)
        
        # Only 'C' matches at position 2
        c_code = ord('C')
        assert result[0, 1, 2] == c_code
        
        # All other positions should be 0 (different letters at those positions)
        assert result[0, 1, 0] == 0  # A vs E
        assert result[0, 1, 1] == 0  # B vs D
        assert result[0, 1, 3] == 0  # D vs B
        assert result[0, 1, 4] == 0  # E vs A
        
        # Common letters section should contain A, B, C, D, E
        common_section = set(result[0, 1, 5:10]) - {0}
        expected_common = {ord('A'), ord('B'), ord('C'), ord('D'), ord('E')}
        assert common_section == expected_common
    
    def test_symmetry(self):
        """Test that the matrix is symmetric: hints[i,j] == hints[j,i]."""
        words = ["apple", "brave", "crane"]
        words_array = words_to_array(words)
        
        result = compute_cross_hints_matrix(words_array)
        
        N = len(words)
        for i in range(N):
            for j in range(N):
                np.testing.assert_array_equal(
                    result[i, j], result[j, i],
                    err_msg=f"Matrix not symmetric at ({i},{j}) vs ({j},{i})"
                )
    
    def test_diagonal_self_match(self):
        """Test diagonal entries (word compared to itself)."""
        words = ["hello", "world", "crane"]
        words_array = words_to_array(words)
        
        result = compute_cross_hints_matrix(words_array)
        
        for i, word in enumerate(words):
            word_upper = word.upper()
            expected_letters = np.array(list(word_upper.encode('utf-8')), dtype=np.uint8)
            
            # First L positions should be the word itself
            np.testing.assert_array_equal(result[i, i, :5], expected_letters)
    
    def test_single_word(self):
        """Test with a single word."""
        words = ["alone"]
        words_array = words_to_array(words)
        
        result = compute_cross_hints_matrix(words_array)
        
        assert result.shape == (1, 1, 10)
        expected = np.array(list("ALONE".encode('utf-8')), dtype=np.uint8)
        np.testing.assert_array_equal(result[0, 0, :5], expected)
    
    def test_partial_overlap(self):
        """Test words with partial letter overlap."""
        words = ["crane", "trace"]  # Both have 'r', 'a', 'c', 'e'
        words_array = words_to_array(words)
        
        result = compute_cross_hints_matrix(words_array)
        
        # Check position matches
        # crane: C R A N E
        # trace: T R A C E
        # Position 1: R matches
        assert result[0, 1, 1] == ord('R')
        # Position 2: A matches  
        assert result[0, 1, 2] == ord('A')
        # Position 4: E matches
        assert result[0, 1, 4] == ord('E')
        
        # Position 0: C vs T - no match
        assert result[0, 1, 0] == 0
        # Position 3: N vs C - no match
        assert result[0, 1, 3] == 0
        
        # Common letters: C, R, A, E (N is not in trace, T is not in crane)
        common_section = set(result[0, 1, 5:10]) - {0}
        expected_common = {ord('C'), ord('R'), ord('A'), ord('E')}
        assert common_section == expected_common
    
    def test_dtype_uint8(self):
        """Test that input and output are uint8 as expected."""
        words = ["test", "best"]
        words_array = words_to_array(words)
        
        assert words_array.dtype == np.uint8
        
        result = compute_cross_hints_matrix(words_array)
        assert result.dtype == np.uint8
    
    def test_three_letter_words(self):
        """Test with shorter words (L=3)."""
        words = ["cat", "bat", "car"]
        words_array = words_to_array(words)
        
        result = compute_cross_hints_matrix(words_array)
        
        # Shape should be (3, 3, 6)
        assert result.shape == (3, 3, 6)
        
        # cat vs bat: positions 1,2 match (A, T)
        assert result[0, 1, 0] == 0  # C vs B
        assert result[0, 1, 1] == ord('A')
        assert result[0, 1, 2] == ord('T')
        
        # cat vs car: positions 0,1 match (C, A)
        assert result[0, 2, 0] == ord('C')
        assert result[0, 2, 1] == ord('A')
        assert result[0, 2, 2] == 0  # T vs R


class TestOptimizedVersions:
    """Tests to verify optimized versions produce equivalent results."""
    
    def test_optimized_matches_original_basic(self):
        """Test that optimized version matches original on basic input."""
        words = ["apple", "brave", "crane"]
        words_array = words_to_array(words)
        
        original = compute_cross_hints_matrix(words_array)
        optimized = compute_cross_hints_matrix_optimized(words_array)
        
        # Position matches should be identical
        np.testing.assert_array_equal(original[:, :, :5], optimized[:, :, :5])
        
        # Common letters may be in different order, check sets match
        L = 5
        N = len(words)
        for i in range(N):
            for j in range(N):
                orig_common = set(original[i, j, L:]) - {0}
                opt_common = set(optimized[i, j, L:]) - {0}
                assert orig_common == opt_common, f"Common letters mismatch at ({i},{j})"
    
    def test_fast_matches_original_basic(self):
        """Test that fast version matches original on basic input."""
        words = ["apple", "brave", "crane"]
        words_array = words_to_array(words)
        
        original = compute_cross_hints_matrix(words_array)
        fast = compute_cross_hints_matrix_fast(words_array)
        
        # Position matches should be identical
        np.testing.assert_array_equal(original[:, :, :5], fast[:, :, :5])
        
        # Common letters may be in different order, check sets match
        L = 5
        N = len(words)
        for i in range(N):
            for j in range(N):
                orig_common = set(original[i, j, L:]) - {0}
                fast_common = set(fast[i, j, L:]) - {0}
                assert orig_common == fast_common, f"Common letters mismatch at ({i},{j})"
    
    def test_optimized_larger_input(self):
        """Test optimized versions on larger input."""
        words = [
            "apple", "brave", "crane", "doubt", "eagle",
            "flint", "grape", "honey", "input", "jumpy"
        ]
        words_array = words_to_array(words)
        
        original = compute_cross_hints_matrix(words_array)
        optimized = compute_cross_hints_matrix_optimized(words_array)
        fast = compute_cross_hints_matrix_fast(words_array)
        
        L = 5
        N = len(words)
        
        # Position matches should be identical for all versions
        np.testing.assert_array_equal(original[:, :, :L], optimized[:, :, :L])
        np.testing.assert_array_equal(original[:, :, :L], fast[:, :, :L])
        
        # Check common letters match for all pairs
        for i in range(N):
            for j in range(N):
                orig_common = set(original[i, j, L:]) - {0}
                opt_common = set(optimized[i, j, L:]) - {0}
                fast_common = set(fast[i, j, L:]) - {0}
                assert orig_common == opt_common, f"Optimized mismatch at ({i},{j})"
                assert orig_common == fast_common, f"Fast mismatch at ({i},{j})"
    
    def test_optimized_symmetry(self):
        """Test that optimized versions produce symmetric results."""
        words = ["apple", "brave", "crane", "doubt"]
        words_array = words_to_array(words)
        
        optimized = compute_cross_hints_matrix_optimized(words_array)
        fast = compute_cross_hints_matrix_fast(words_array)
        
        N = len(words)
        for i in range(N):
            for j in range(N):
                np.testing.assert_array_equal(optimized[i, j], optimized[j, i])
                np.testing.assert_array_equal(fast[i, j], fast[j, i])
    
    def test_optimized_single_word(self):
        """Test optimized versions with single word."""
        words = ["alone"]
        words_array = words_to_array(words)
        
        optimized = compute_cross_hints_matrix_optimized(words_array)
        fast = compute_cross_hints_matrix_fast(words_array)
        
        assert optimized.shape == (1, 1, 10)
        assert fast.shape == (1, 1, 10)
        
        expected = np.array(list("ALONE".encode('utf-8')), dtype=np.uint8)
        np.testing.assert_array_equal(optimized[0, 0, :5], expected)
        np.testing.assert_array_equal(fast[0, 0, :5], expected)
    
    def test_optimized_no_common_letters(self):
        """Test optimized versions with words having no common letters."""
        words = ["abcde", "fghij"]
        words_array = words_to_array(words)
        
        optimized = compute_cross_hints_matrix_optimized(words_array)
        fast = compute_cross_hints_matrix_fast(words_array)
        
        # No matching positions
        assert np.all(optimized[0, 1, :5] == 0)
        assert np.all(fast[0, 1, :5] == 0)
        
        # No common letters
        assert np.all(optimized[0, 1, 5:] == 0)
        assert np.all(fast[0, 1, 5:] == 0)
    
    def test_optimized_dtype(self):
        """Test that optimized versions return uint8."""
        words = ["test", "best"]
        words_array = words_to_array(words)
        
        optimized = compute_cross_hints_matrix_optimized(words_array)
        fast = compute_cross_hints_matrix_fast(words_array)
        
        assert optimized.dtype == np.uint8
        assert fast.dtype == np.uint8
    
    def test_optimized_three_letter_words(self):
        """Test optimized versions with shorter words."""
        words = ["cat", "bat", "car"]
        words_array = words_to_array(words)
        
        original = compute_cross_hints_matrix(words_array)
        optimized = compute_cross_hints_matrix_optimized(words_array)
        fast = compute_cross_hints_matrix_fast(words_array)
        
        # Shape should be (3, 3, 6)
        assert optimized.shape == (3, 3, 6)
        assert fast.shape == (3, 3, 6)
        
        # Position matches should be identical
        np.testing.assert_array_equal(original[:, :, :3], optimized[:, :, :3])
        np.testing.assert_array_equal(original[:, :, :3], fast[:, :, :3])


class TestPerformance:
    """Performance benchmarks for comparing implementations."""
    
    @pytest.mark.parametrize("n_words", [50, 100, 500])
    def test_benchmark_comparison(self, n_words):
        """Benchmark all implementations on larger datasets."""
        import time
        
        # Generate random 5-letter words
        np.random.seed(42)
        words_array = np.random.randint(65, 91, size=(n_words, 5), dtype=np.uint8)
        
        # Warm up Numba JIT if available (first call compiles)
        if NUMBA_AVAILABLE:
            _ = compute_cross_hints_matrix_numba(words_array[:5])
            _ = compute_cross_hints_matrix_numba_parallel(words_array[:5])
        
        # Benchmark original (skip for large N to save time)
        if n_words <= 100:
            start = time.perf_counter()
            original = compute_cross_hints_matrix(words_array)
            time_original = time.perf_counter() - start
        else:
            time_original = None
            original = None
        
        # Benchmark optimized
        start = time.perf_counter()
        optimized = compute_cross_hints_matrix_optimized(words_array)
        time_optimized = time.perf_counter() - start
        
        # Benchmark fast
        start = time.perf_counter()
        fast = compute_cross_hints_matrix_fast(words_array)
        time_fast = time.perf_counter() - start
        
        print(f"\n{n_words} words benchmark:")
        if time_original:
            print(f"  Original:       {time_original:.4f}s (baseline)")
            baseline = time_original
        else:
            print(f"  Original:       (skipped for large N)")
            baseline = time_fast  # Use fast as baseline for comparison
        print(f"  Optimized:      {time_optimized:.4f}s ({baseline/time_optimized:.1f}x)")
        print(f"  Fast:           {time_fast:.4f}s ({baseline/time_fast:.1f}x)")
        
        # Benchmark numba versions if available
        if NUMBA_AVAILABLE:
            start = time.perf_counter()
            numba_result = compute_cross_hints_matrix_numba(words_array)
            time_numba = time.perf_counter() - start
            
            start = time.perf_counter()
            numba_parallel = compute_cross_hints_matrix_numba_parallel(words_array)
            time_numba_parallel = time.perf_counter() - start
            
            print(f"  Numba:          {time_numba:.4f}s ({baseline/time_numba:.1f}x)")
            print(f"  Numba Parallel: {time_numba_parallel:.4f}s ({baseline/time_numba_parallel:.1f}x)")
            
            # Verify correctness
            L = 5
            np.testing.assert_array_equal(fast[:, :, :L], numba_result[:, :, :L])
            np.testing.assert_array_equal(fast[:, :, :L], numba_parallel[:, :, :L])
            
            # Common letters sets should match
            N = n_words
            for i in range(min(N, 10)):
                for j in range(min(N, 10)):
                    fast_common = set(fast[i, j, L:]) - {0}
                    numba_common = set(numba_result[i, j, L:]) - {0}
                    assert fast_common == numba_common, f"Numba mismatch at ({i},{j})"
        else:
            print(f"  Numba:          (not installed)")
            print(f"  Numba Parallel: (not installed)")