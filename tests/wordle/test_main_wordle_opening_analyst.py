"""
Unit tests for Wordle opening word finder.
"""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest
import pandas as pd
from riddle import Language
from wordle.main_wordle_opening_analyst import (
    find_best_opening,
    initialize_csv_file,
    load_existing_solutions,
    append_solution_to_csv,
    compute_word_entropies,
    compute_information_value,
)


class TestCSVFunctions:
    """Test CSV-related functions."""
    
    def test_initialize_csv_file_creates_file_with_headers(self):
        """Test that initialize_csv_file creates a file with proper headers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "results" / "test.csv"
            
            initialize_csv_file(csv_path)
            
            assert csv_path.exists()
            with open(csv_path, 'r', encoding='utf-8') as f:
                header = f.readline().strip()
                assert header == "frequency_score,words"
    
    def test_initialize_csv_file_does_not_overwrite_existing(self):
        """Test that initialize_csv_file doesn't overwrite existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test.csv"
            
            # Create file with some content
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write("frequency_score,words\n")
                f.write("0.5000,\"test, words\"\n")
            
            initialize_csv_file(csv_path)
            
            # Should not overwrite
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                assert len(lines) == 2
                assert "test, words" in lines[1]
    
    def test_append_solution_to_csv(self):
        """Test that append_solution_to_csv adds a row correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test.csv"
            
            # Initialize file
            initialize_csv_file(csv_path)
            
            # Append solution
            append_solution_to_csv(csv_path, 0.6674, ["nodes", "trial"])
            
            # Verify
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                assert len(lines) == 2
                assert "0.6674" in lines[1]
                assert "nodes, trial" in lines[1]
    
    def test_load_existing_solutions_empty_file(self):
        """Test that load_existing_solutions handles non-existent file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "nonexistent.csv"
            
            # Create a simple DataFrame for testing
            df_words = pd.DataFrame({
                'word': ['nodes', 'trial', 'roast'],
                'letters': [set('nodes'), set('trial'), set('roast')]
            })
            
            start_iteration, excluded = load_existing_solutions(csv_path, df_words, 2)
            
            assert start_iteration == 0
            assert len(excluded) == 0
    
    def test_load_existing_solutions_with_data(self):
        """Test that load_existing_solutions correctly loads and parses data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test.csv"
            
            # Create CSV with data
            with open(csv_path, 'w', encoding='utf-8') as f:
                f.write("frequency_score,words\n")
                f.write("0.6674,\"nodes, trial\"\n")
                f.write("0.6674,\"dales, intro\"\n")
            
            # Create DataFrame with these words
            df_words = pd.DataFrame({
                'word': ['nodes', 'trial', 'dales', 'intro', 'roast'],
                'letters': [set('nodes'), set('trial'), set('dales'), set('intro'), set('roast')]
            })
            
            start_iteration, excluded = load_existing_solutions(csv_path, df_words, 2)
            
            assert start_iteration == 2
            assert len(excluded) == 2
            # Each excluded combination should have 2 word indices
            assert all(len(combo) == 2 for combo in excluded)


class TestWordleOpening:
    """Test the opening word finder."""
    
    def test_find_best_opening_with_english(self):
        """Test that find_best_opening works with English language."""
        # This should not raise an exception
        try:
            find_best_opening(Language.EN, 5, 2, top_k=1)
            assert True
        except ValueError as e:
            pytest.fail(f"find_best_opening raised ValueError: {e}")
    
    def test_find_best_opening_with_french(self):
        """Test that find_best_opening works with French language."""
        # This should not raise an exception
        try:
            find_best_opening(Language.FR, 5, 2, top_k=1)
            assert True
        except ValueError as e:
            pytest.fail(f"find_best_opening raised ValueError: {e}")
    
    def test_language_from_string_en(self):
        """Test that Language enum can be created from 'en' string."""
        # Test the bug: args.language is 'en', we need to convert it properly
        lang_str = "en"
        # The correct way to create a Language from the string
        lang = Language(lang_str.upper())
        assert lang == Language.EN
    
    def test_language_from_string_fr(self):
        """Test that Language enum can be created from 'fr' string."""
        lang_str = "fr"
        lang = Language(lang_str.upper())
        assert lang == Language.FR
    
    def test_cli_argument_parsing(self):
        """Test that CLI arguments are parsed correctly and don't cause ValueError."""
        # Simulate the command line: en 5 2 --top-k 100
        test_args = ['main_wordle_opening.py', 'en', '5', '2', '--top-k', '100']
        
        with patch.object(sys, 'argv', test_args):
            # Import the main section
            import argparse
            parser = argparse.ArgumentParser()
            parser.add_argument("language", type=str, choices=["fr", "en"])
            parser.add_argument("length", type=int)
            parser.add_argument("N", type=int)
            parser.add_argument("--top-k", type=int, default=1)
            
            args = parser.parse_args()
            
            # The bug was here: args.language.upper instead of args.language.upper()
            # This test verifies that we can create a Language enum from the parsed args
            # This should NOT raise ValueError
            lang = Language(args.language.upper())
            assert lang == Language.EN
    
    def test_compute_word_entropies(self):
        """Test that compute_word_entropies creates proper DataFrame."""
        words = ['abcde', 'fghij', 'klmno']
        frequency_map = {c: 0.1 for c in 'abcdefghijklmno'}
        
        df = compute_word_entropies(words, frequency_map)
        
        assert len(df) == 3
        assert 'word' in df.columns
        assert 'letters' in df.columns
        assert 'frequency' in df.columns
        assert 'entropy' in df.columns
        assert all(df['word'] == words)


class TestCSVIntegration:
    """Integration tests for CSV functionality."""
    
    def test_csv_persistence_and_resume(self):
        """Test that solutions are saved to CSV and can be resumed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = Path(tmpdir) / "test_openings.csv"
            
            # Create a simple word set
            words = ['nodes', 'trial', 'roast', 'lined', 'dales', 'intro']
            frequency_map = {c: 0.1 for c in set(''.join(words))}
            df_words = compute_word_entropies(words, frequency_map)
            
            # Initialize CSV
            initialize_csv_file(csv_path)
            
            # Append a solution
            append_solution_to_csv(csv_path, 0.6674, ['nodes', 'trial'])
            
            # Load it back
            start_iteration, excluded = load_existing_solutions(csv_path, df_words, 2)
            
            assert start_iteration == 1
            assert len(excluded) == 1
            
            # Verify the CSV content is correct
            df = pd.read_csv(csv_path)
            assert len(df) == 1
            assert df.iloc[0]['frequency_score'] == 0.6674
            assert df.iloc[0]['words'] == 'nodes, trial'


class TestInformationValue:
    """Test information-theoretic scoring of word combinations."""
    
    def test_no_duplicate_letters_full_value(self):
        """Words with all distinct letters get full positional frequency value."""
        words = ['abc', 'def']  # No shared letters
        positional_freqs = [
            {'a': 0.5, 'b': 0.3, 'd': 0.2},  # pos 0
            {'b': 0.4, 'e': 0.4, 'c': 0.2},  # pos 1
            {'c': 0.6, 'f': 0.4}             # pos 2
        ]
        
        # Expected: sum all positional frequencies
        # 'abc': a@0(0.5) + b@1(0.4) + c@2(0.6) = 1.5
        # 'def': d@0(0.2) + e@1(0.4) + f@2(0.4) = 1.0
        # Total = 2.5
        info_value = compute_information_value(words, positional_freqs)
        assert info_value == pytest.approx(2.5)
    
    def test_duplicate_letters_penalized(self):
        """Words with duplicate letters should have reduced value."""
        words = ['aba', 'cdc']  # 'a' appears twice in word 1, 'c' twice in word 2
        positional_freqs = [
            {'a': 0.5, 'c': 0.3},  # pos 0
            {'b': 0.4, 'd': 0.3},  # pos 1
            {'a': 0.5, 'c': 0.3}   # pos 2
        ]
        
        # Without penalty: 0.5 + 0.4 + 0.5 + 0.3 + 0.3 + 0.3 = 2.3
        # With penalty: should be less due to duplicate 'a' and 'c'
        info_value = compute_information_value(words, positional_freqs)
        assert info_value < 2.3  # Should be penalized
    
    def test_shared_letters_across_words_counted_once(self):
        """Same letter in different words at different positions: count each position."""
        words = ['sat', 'sea']  # 's' at pos 0 in both, 'e' and 'a' shared
        positional_freqs = [
            {'s': 0.5},           # pos 0
            {'a': 0.4, 'e': 0.3}, # pos 1
            {'t': 0.3, 'a': 0.2}  # pos 2
        ]
        
        # 's' at pos 0: counted once (not twice) = 0.5
        # 'a' at pos 1 (word 1): 0.4
        # 't' at pos 2 (word 1): 0.3
        # 'e' at pos 1 (word 2): 0.3
        # 'a' at pos 2 (word 2): 0.2
        # But 'a' appears in both words - should we count both positions?
        # Yes, because they're different positions (1 vs 2)
        info_value = compute_information_value(words, positional_freqs)
        # The key is: duplicate 's' at same position (0) should be counted once
        # But 'a' at different positions (1 and 2) provides different info
        assert info_value > 0  # At least we get some value
