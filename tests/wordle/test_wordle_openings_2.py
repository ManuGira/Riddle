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
    evaluate_opening_entropy,
    evaluate_opening_entropy_optimized,
    evaluate_opening_entropy_numba,
    evaluate_opening_entropy_numba_parallel,
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


def get_all_cross_hints_implementations():
    """Get all compute_cross_hints_matrix implementations for parametrized testing."""
    implementations = [
        ("original", compute_cross_hints_matrix),
        ("optimized", compute_cross_hints_matrix_optimized),
        ("fast", compute_cross_hints_matrix_fast),
    ]
    if NUMBA_AVAILABLE:
        implementations.extend([
            ("numba", compute_cross_hints_matrix_numba),
            ("numba_parallel", compute_cross_hints_matrix_numba_parallel),
        ])
    return implementations


class TestAllCrossHintsImplementations:
    """Parametrized tests to verify ALL compute_cross_hints_matrix implementations produce equivalent results."""
    
    @pytest.fixture
    def all_implementations(self):
        """Return all available implementations."""
        return get_all_cross_hints_implementations()
    
    def _assert_results_equivalent(self, result1, result2, name1, name2, L):
        """Assert that two hint matrices are equivalent (position matches identical, common letters same set)."""
        N = result1.shape[0]
        
        # Position matches should be identical
        np.testing.assert_array_equal(
            result1[:, :, :L], result2[:, :, :L],
            err_msg=f"Position matches differ between {name1} and {name2}"
        )
        
        # Common letters may be in different order, check sets match
        for i in range(N):
            for j in range(N):
                common1 = set(result1[i, j, L:]) - {0}
                common2 = set(result2[i, j, L:]) - {0}
                assert common1 == common2, \
                    f"Common letters mismatch at ({i},{j}) between {name1} and {name2}: {common1} vs {common2}"
    
    def test_all_implementations_match_basic(self, all_implementations):
        """Test all implementations produce equivalent results on basic input."""
        words = ["apple", "brave", "crane"]
        words_array = words_to_array(words)
        L = 5
        
        # Get reference result from first implementation
        ref_name, ref_func = all_implementations[0]
        ref_result = ref_func(words_array)
        
        # Compare all other implementations to reference
        for name, func in all_implementations[1:]:
            result = func(words_array)
            self._assert_results_equivalent(ref_result, result, ref_name, name, L)
    
    def test_all_implementations_match_larger(self, all_implementations):
        """Test all implementations on a larger word set."""
        words = [
            "apple", "brave", "crane", "doubt", "eagle",
            "flint", "grape", "honey", "input", "jumpy"
        ]
        words_array = words_to_array(words)
        L = 5
        
        ref_name, ref_func = all_implementations[0]
        ref_result = ref_func(words_array)
        
        for name, func in all_implementations[1:]:
            result = func(words_array)
            self._assert_results_equivalent(ref_result, result, ref_name, name, L)
    
    def test_all_implementations_shape_and_dtype(self, all_implementations):
        """Test all implementations return correct shape and dtype."""
        words = ["apple", "brave", "crane"]
        words_array = words_to_array(words)
        N, L = len(words), 5
        
        for name, func in all_implementations:
            result = func(words_array)
            assert result.shape == (N, N, 2 * L), f"{name} has wrong shape: {result.shape}"
            assert result.dtype == np.uint8, f"{name} has wrong dtype: {result.dtype}"
    
    def test_all_implementations_symmetry(self, all_implementations):
        """Test all implementations produce symmetric matrices."""
        words = ["apple", "brave", "crane", "doubt"]
        words_array = words_to_array(words)
        N = len(words)
        
        for name, func in all_implementations:
            result = func(words_array)
            for i in range(N):
                for j in range(N):
                    np.testing.assert_array_equal(
                        result[i, j], result[j, i],
                        err_msg=f"{name} not symmetric at ({i},{j}) vs ({j},{i})"
                    )
    
    def test_all_implementations_single_word(self, all_implementations):
        """Test all implementations with single word."""
        words = ["alone"]
        words_array = words_to_array(words)
        expected = np.array(list("ALONE".encode('utf-8')), dtype=np.uint8)
        
        for name, func in all_implementations:
            result = func(words_array)
            assert result.shape == (1, 1, 10), f"{name} wrong shape for single word"
            np.testing.assert_array_equal(
                result[0, 0, :5], expected,
                err_msg=f"{name} wrong position matches for single word"
            )
    
    def test_all_implementations_no_common_letters(self, all_implementations):
        """Test all implementations with words having no common letters."""
        words = ["abcde", "fghij"]
        words_array = words_to_array(words)
        
        for name, func in all_implementations:
            result = func(words_array)
            # No matching positions
            assert np.all(result[0, 1, :5] == 0), f"{name} should have no position matches"
            # No common letters
            assert np.all(result[0, 1, 5:] == 0), f"{name} should have no common letters"
    
    def test_all_implementations_three_letter_words(self, all_implementations):
        """Test all implementations with shorter words (L=3)."""
        words = ["cat", "bat", "car"]
        words_array = words_to_array(words)
        L = 3
        
        ref_name, ref_func = all_implementations[0]
        ref_result = ref_func(words_array)
        
        for name, func in all_implementations[1:]:
            result = func(words_array)
            assert result.shape == (3, 3, 6), f"{name} wrong shape for 3-letter words"
            self._assert_results_equivalent(ref_result, result, ref_name, name, L)
    
    def test_all_implementations_real_words(self, all_implementations):
        """Test all implementations with real words from the word list."""
        from riddle import DATA_FOLDER_PATH
        words_file = DATA_FOLDER_PATH / "words_lists" / "wordle_list_EN_L5_base.txt"
        with open(words_file, encoding="utf-8") as f:
            words = [w.strip().upper() for w in f if w.strip()][:20]
        
        words_array = words_to_array(words)
        L = 5
        
        ref_name, ref_func = all_implementations[0]
        ref_result = ref_func(words_array)
        
        for name, func in all_implementations[1:]:
            result = func(words_array)
            self._assert_results_equivalent(ref_result, result, ref_name, name, L)
    
    @pytest.mark.skipif(not NUMBA_AVAILABLE, reason="Numba not available")
    def test_numba_implementations_available(self):
        """Test that Numba implementations are available when Numba is installed."""
        words = ["apple", "brave"]
        words_array = words_to_array(words)
        
        # These should not raise
        result_numba = compute_cross_hints_matrix_numba(words_array)
        result_parallel = compute_cross_hints_matrix_numba_parallel(words_array)
        
        assert result_numba.shape == (2, 2, 10)
        assert result_parallel.shape == (2, 2, 10)


class TestEvaluateOpeningEntropy:
    """Unit tests for evaluate_opening_entropy function."""
    
    def test_single_opening_word(self):
        """Test with a single opening word."""
        words_list = ["APPLE", "APPLY", "AMPLE", "MAPLE", "PLANE"]
        words_array = words_to_array(words_list)
        hint_matrix = compute_cross_hints_matrix_fast(words_array)
        
        from wordle.wordle_openings_2 import evaluate_opening_entropy
        opening_indices = [0]  # "APPLE"
        
        entropy, remaining = evaluate_opening_entropy(
            words_array, hint_matrix, opening_indices
        )
        
        # Basic sanity checks
        assert entropy > 0, "Entropy should be positive"
        assert 0 < remaining <= len(words_list), "Remaining words should be in valid range"
        assert isinstance(entropy, (float, np.floating)), "Entropy should be float"
        assert isinstance(remaining, (float, np.floating)), "Remaining words should be float"
    
    def test_multiple_opening_words(self):
        """Test with multiple opening words."""
        words_list = ["APPLE", "APPLY", "AMPLE", "MAPLE", "PLANE"]
        words_array = words_to_array(words_list)
        hint_matrix = compute_cross_hints_matrix_fast(words_array)
        
        from wordle.wordle_openings_2 import evaluate_opening_entropy
        opening_indices = [0, 2]  # "APPLE", "AMPLE"
        
        entropy, remaining = evaluate_opening_entropy(
            words_array, hint_matrix, opening_indices
        )
        
        assert entropy > 0, "Entropy should be positive"
        assert 0 < remaining <= len(words_list), "Remaining words should be in valid range"
    
    def test_more_openings_increases_entropy(self):
        """Test that more opening words increase total entropy."""
        words_list = ["CRANE", "SLATE", "STORY", "FJORD", "WIMPY"]
        words_array = words_to_array(words_list)
        hint_matrix = compute_cross_hints_matrix_fast(words_array)
        
        from wordle.wordle_openings_2 import evaluate_opening_entropy
        
        # Single opening word
        entropy_1, _ = evaluate_opening_entropy(
            words_array, hint_matrix, [0]
        )
        
        # Two opening words
        entropy_2, _ = evaluate_opening_entropy(
            words_array, hint_matrix, [0, 1]
        )
        
        # More opening words should increase entropy
        assert entropy_2 > entropy_1, "More opening words should increase entropy"
    
    def test_different_word_orders_same_result(self):
        """Test that order of opening words doesn't matter."""
        words_list = ["APPLE", "APPLY", "AMPLE", "MAPLE", "PLANE"]
        words_array = words_to_array(words_list)
        hint_matrix = compute_cross_hints_matrix_fast(words_array)
        
        from wordle.wordle_openings_2 import evaluate_opening_entropy
        
        entropy_1, remaining_1 = evaluate_opening_entropy(
            words_array, hint_matrix, [0, 2, 3]
        )
        
        entropy_2, remaining_2 = evaluate_opening_entropy(
            words_array, hint_matrix, [3, 0, 2]
        )
        
        # Results should be identical regardless of order
        assert np.isclose(entropy_1, entropy_2), "Order shouldn't affect entropy"
        assert np.isclose(remaining_1, remaining_2), "Order shouldn't affect remaining words"
    
    def test_empty_opening_list(self):
        """Test with no opening words."""
        words_list = ["APPLE", "APPLY", "AMPLE", "MAPLE", "PLANE"]
        words_array = words_to_array(words_list)
        hint_matrix = compute_cross_hints_matrix_fast(words_array)
        
        from wordle.wordle_openings_2 import evaluate_opening_entropy
        
        entropy, remaining = evaluate_opening_entropy(
            words_array, hint_matrix, []
        )
        
        # With no hints, all words should remain and entropy should be 0 (no information gained)
        assert np.isclose(remaining, len(words_list)), "All words should remain with no opening"
        assert entropy == 0.0, "Entropy should be 0 with no opening words"
    
    def test_entropy_bounds(self):
        """Test that entropy is within reasonable bounds."""
        words_list = ["CRANE", "SLATE", "STORY", "FJORD", "WIMPY"]
        words_array = words_to_array(words_list)
        hint_matrix = compute_cross_hints_matrix_fast(words_array)
        N = len(words_list)
        
        from wordle.wordle_openings_2 import evaluate_opening_entropy
        
        opening_indices = [0, 1]
        entropy, _ = evaluate_opening_entropy(
            words_array, hint_matrix, opening_indices
        )
        
        # Entropy should be at most log2(N) per word on average (with some margin)
        max_entropy = np.log2(N)
        assert 0 < entropy <= max_entropy * 1.5, f"Entropy {entropy} should be reasonable"
    
    def test_remaining_words_bounds(self):
        """Test that remaining words are within bounds."""
        words_list = ["CRANE", "SLATE", "STORY", "FJORD", "WIMPY"]
        words_array = words_to_array(words_list)
        hint_matrix = compute_cross_hints_matrix_fast(words_array)
        N = len(words_list)
        
        from wordle.wordle_openings_2 import evaluate_opening_entropy
        
        opening_indices = [0, 1, 2]
        _, remaining = evaluate_opening_entropy(
            words_array, hint_matrix, opening_indices
        )
        
        # Remaining words should be between 1 and N
        assert 1 <= remaining <= N, f"Remaining words {remaining} should be in [1, {N}]"
    
    def test_with_identical_words(self):
        """Test behavior with some identical words."""
        words_list = ["APPLE", "APPLE", "BREAD"]
        words_array = words_to_array(words_list)
        hint_matrix = compute_cross_hints_matrix_fast(words_array)
        
        from wordle.wordle_openings_2 import evaluate_opening_entropy
        
        opening_indices = [0]
        entropy, remaining = evaluate_opening_entropy(
            words_array, hint_matrix, opening_indices
        )
        
        assert entropy > 0, "Should handle identical words"
        assert remaining > 0, "Should have remaining words"
    
    def test_output_no_nan_or_inf(self):
        """Test that outputs are valid numbers (not NaN or inf)."""
        words_list = ["APPLE", "APPLY", "AMPLE", "MAPLE", "PLANE"]
        words_array = words_to_array(words_list)
        hint_matrix = compute_cross_hints_matrix_fast(words_array)
        
        from wordle.wordle_openings_2 import evaluate_opening_entropy
        
        entropy, remaining = evaluate_opening_entropy(
            words_array, hint_matrix, [0, 1]
        )
        
        assert not np.isnan(entropy), "Entropy should not be NaN"
        assert not np.isnan(remaining), "Remaining should not be NaN"
        assert not np.isinf(entropy), "Entropy should not be infinite"
        assert not np.isinf(remaining), "Remaining should not be infinite"
    
    def test_medium_word_list(self):
        """Test with a larger word list."""
        # Load 50 real words from the word list
        from riddle import DATA_FOLDER_PATH
        words_file = DATA_FOLDER_PATH / "words_lists" / "wordle_list_EN_L5_base.txt"
        with open(words_file, encoding="utf-8") as f:
            words_list = [w.strip().upper() for w in f if w.strip()][:50]
        
        words_array = words_to_array(words_list)
        hint_matrix = compute_cross_hints_matrix_fast(words_array)
        
        from wordle.wordle_openings_2 import evaluate_opening_entropy
        
        opening_indices = [0, 10, 20]
        entropy, remaining = evaluate_opening_entropy(
            words_array, hint_matrix, opening_indices
        )
        
        assert entropy > 0, "Entropy should be positive"
        assert 0 < remaining <= len(words_list), "Remaining words in valid range"
        
        # With 50 words and 3 opening words, should narrow down significantly
        assert remaining < len(words_list), "Should reduce word space"


class TestEvaluateOpeningEntropyImplementations:
    """Test that all evaluate_opening_entropy implementations produce identical results."""
    
    def _get_implementations(self):
        """Get list of all implementations to test."""
        implementations = [
            ("original", evaluate_opening_entropy),
            ("optimized", evaluate_opening_entropy_optimized),
        ]
        if NUMBA_AVAILABLE:
            implementations.extend([
                ("numba", evaluate_opening_entropy_numba),
                ("numba_parallel", evaluate_opening_entropy_numba_parallel),
            ])
        return implementations
    
    def test_implementations_match_small(self):
        """Test all implementations produce same results with small word list."""
        words_list = ["APPLE", "APPLY", "AMPLE", "MAPLE", "PLANE"]
        words_array = words_to_array(words_list)
        hint_matrix = compute_cross_hints_matrix_fast(words_array)
        opening_indices = [0, 2]
        
        implementations = self._get_implementations()
        ref_name, ref_func = implementations[0]
        ref_entropy, ref_remaining = ref_func(words_array, hint_matrix, opening_indices)
        
        for name, func in implementations[1:]:
            entropy, remaining = func(words_array, hint_matrix, opening_indices)
            assert np.isclose(entropy, ref_entropy, rtol=1e-5), \
                f"{name} entropy {entropy} != {ref_name} {ref_entropy}"
            assert np.isclose(remaining, ref_remaining, rtol=1e-5), \
                f"{name} remaining {remaining} != {ref_name} {ref_remaining}"
    
    def test_implementations_match_medium(self):
        """Test all implementations with 50 words."""
        from riddle import DATA_FOLDER_PATH
        words_file = DATA_FOLDER_PATH / "words_lists" / "wordle_list_EN_L5_base.txt"
        with open(words_file, encoding="utf-8") as f:
            words_list = [w.strip().upper() for w in f if w.strip()][:50]
        
        words_array = words_to_array(words_list)
        hint_matrix = compute_cross_hints_matrix_fast(words_array)
        opening_indices = [0, 10]
        
        implementations = self._get_implementations()
        ref_name, ref_func = implementations[0]
        ref_entropy, ref_remaining = ref_func(words_array, hint_matrix, opening_indices)
        
        for name, func in implementations[1:]:
            entropy, remaining = func(words_array, hint_matrix, opening_indices)
            assert np.isclose(entropy, ref_entropy, rtol=1e-5), \
                f"{name} entropy {entropy} != {ref_name} {ref_entropy}"
            assert np.isclose(remaining, ref_remaining, rtol=1e-5), \
                f"{name} remaining {remaining} != {ref_name} {ref_remaining}"
    
    def test_implementations_match_single_opening(self):
        """Test all implementations with single opening word."""
        from riddle import DATA_FOLDER_PATH
        words_file = DATA_FOLDER_PATH / "words_lists" / "wordle_list_EN_L5_base.txt"
        with open(words_file, encoding="utf-8") as f:
            words_list = [w.strip().upper() for w in f if w.strip()][:30]
        
        words_array = words_to_array(words_list)
        hint_matrix = compute_cross_hints_matrix_fast(words_array)
        opening_indices = [5]  # Single opening word
        
        implementations = self._get_implementations()
        ref_name, ref_func = implementations[0]
        ref_entropy, ref_remaining = ref_func(words_array, hint_matrix, opening_indices)
        
        for name, func in implementations[1:]:
            entropy, remaining = func(words_array, hint_matrix, opening_indices)
            assert np.isclose(entropy, ref_entropy, rtol=1e-5), \
                f"{name} entropy {entropy} != {ref_name} {ref_entropy}"
            assert np.isclose(remaining, ref_remaining, rtol=1e-5), \
                f"{name} remaining {remaining} != {ref_name} {ref_remaining}"
    
    def test_implementations_match_triple_opening(self):
        """Test all implementations with three opening words."""
        from riddle import DATA_FOLDER_PATH
        words_file = DATA_FOLDER_PATH / "words_lists" / "wordle_list_EN_L5_base.txt"
        with open(words_file, encoding="utf-8") as f:
            words_list = [w.strip().upper() for w in f if w.strip()][:40]
        
        words_array = words_to_array(words_list)
        hint_matrix = compute_cross_hints_matrix_fast(words_array)
        opening_indices = [0, 15, 30]
        
        implementations = self._get_implementations()
        ref_name, ref_func = implementations[0]
        ref_entropy, ref_remaining = ref_func(words_array, hint_matrix, opening_indices)
        
        for name, func in implementations[1:]:
            entropy, remaining = func(words_array, hint_matrix, opening_indices)
            assert np.isclose(entropy, ref_entropy, rtol=1e-5), \
                f"{name} entropy {entropy} != {ref_name} {ref_entropy}"
            assert np.isclose(remaining, ref_remaining, rtol=1e-5), \
                f"{name} remaining {remaining} != {ref_name} {ref_remaining}"
    
    def test_implementations_match_empty_opening(self):
        """Test all implementations with no opening words."""
        words_list = ["APPLE", "APPLY", "AMPLE", "MAPLE", "PLANE"]
        words_array = words_to_array(words_list)
        hint_matrix = compute_cross_hints_matrix_fast(words_array)
        opening_indices = []
        
        implementations = self._get_implementations()
        ref_name, ref_func = implementations[0]
        ref_entropy, ref_remaining = ref_func(words_array, hint_matrix, opening_indices)
        
        for name, func in implementations[1:]:
            entropy, remaining = func(words_array, hint_matrix, opening_indices)
            assert np.isclose(entropy, ref_entropy, rtol=1e-5), \
                f"{name} entropy {entropy} != {ref_name} {ref_entropy}"
            assert np.isclose(remaining, ref_remaining, rtol=1e-5), \
                f"{name} remaining {remaining} != {ref_name} {ref_remaining}"
    
    @pytest.mark.skipif(not NUMBA_AVAILABLE, reason="Numba not available")
    def test_numba_versions_no_nan_inf(self):
        """Test that Numba versions don't produce NaN or inf."""
        from riddle import DATA_FOLDER_PATH
        words_file = DATA_FOLDER_PATH / "words_lists" / "wordle_list_EN_L5_base.txt"
        with open(words_file, encoding="utf-8") as f:
            words_list = [w.strip().upper() for w in f if w.strip()][:100]
        
        words_array = words_to_array(words_list)
        hint_matrix = compute_cross_hints_matrix_fast(words_array)
        opening_indices = [0, 25, 50]
        
        for name, func in [("numba", evaluate_opening_entropy_numba), 
                           ("numba_parallel", evaluate_opening_entropy_numba_parallel)]:
            entropy, remaining = func(words_array, hint_matrix, opening_indices)
            assert not np.isnan(entropy), f"{name} produced NaN entropy"
            assert not np.isnan(remaining), f"{name} produced NaN remaining"
            assert not np.isinf(entropy), f"{name} produced inf entropy"
            assert not np.isinf(remaining), f"{name} produced inf remaining"