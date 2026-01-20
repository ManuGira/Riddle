
import tempfile
import pytest
from pathlib import Path

from riddle import DATA_FOLDER_PATH
from riddle.lexicon_parser import LexiconEN, LexiconFR, Grammar, HeadersDF


@pytest.fixture(scope="module")
def temp_en_lexicon():
    """Create a temporary English lexicon file with first 1000 lines for faster testing."""
    lexicon_path = DATA_FOLDER_PATH / "OpenLexicon_EN.tsv"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False, encoding='utf-8') as tmp:
        with open(lexicon_path, 'r', encoding='utf-8') as src:
            # Copy header and first 1000 data lines
            for i, line in enumerate(src):
                if i <= 1000:  # header + 1000 lines
                    tmp.write(line)
                else:
                    break
        tmp_path = tmp.name
    
    yield Path(tmp_path)
    
    # Cleanup
    Path(tmp_path).unlink()


@pytest.fixture(scope="module")
def temp_fr_lexicon():
    """Create a temporary French lexicon file with first 1000 lines for faster testing."""
    lexicon_path = DATA_FOLDER_PATH / "OpenLexicon_FR.tsv"
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False, encoding='utf-8') as tmp:
        with open(lexicon_path, 'r', encoding='utf-8') as src:
            # Copy header and first 1000 data lines
            for i, line in enumerate(src):
                if i <= 1000:  # header + 1000 lines
                    tmp.write(line)
                else:
                    break
        tmp_path = tmp.name
    
    yield Path(tmp_path)
    
    # Cleanup
    Path(tmp_path).unlink()


class TestLexiconEN:
    """Tests for English lexicon parser"""

    def test_load_english_lexicon(self, temp_en_lexicon):
        """Test loading English lexicon file"""
        df = LexiconEN.load(temp_en_lexicon)
        
        # Check dataframe is not empty
        assert len(df) > 0
        
        # Check expected columns exist
        assert HeadersDF.ORTHO in df.columns
        assert HeadersDF.GRAMMAR in df.columns
    
    def test_english_lexicon_contains_words(self, temp_en_lexicon):
        """Test that specific words exist in the English lexicon"""
        df = LexiconEN.load(temp_en_lexicon)
        
        # Check some words exist (first 1000 rows are mostly proper nouns)
        words = df[HeadersDF.ORTHO].values
        assert len(words) > 0
        # First 1000 should have proper nouns starting with capitals
        assert any(word[0].isupper() for word in words if word)
    
    def test_english_grammar_parsing(self, temp_en_lexicon):
        """Test that grammar is correctly parsed and mapped"""
        df = LexiconEN.load(temp_en_lexicon)
        
        # Check _grammar has expected values
        grammar_values = set(df[HeadersDF.GRAMMAR].unique())
        # First 1000 rows will have at least proper nouns
        assert Grammar.PROPER_NOUN in grammar_values or Grammar.NOUN in grammar_values


class TestLexiconFR:
    """Tests for French lexicon parser"""

    def test_load_french_lexicon(self, temp_fr_lexicon):
        """Test loading French lexicon file"""
        df = LexiconFR.load(temp_fr_lexicon)
        
        # Check dataframe is not empty
        assert len(df) > 0
        
        # Check expected columns exist
        assert HeadersDF.ORTHO in df.columns
        assert HeadersDF.GRAMMAR in df.columns
    
    def test_french_lexicon_contains_words(self, temp_fr_lexicon):
        """Test that specific words exist in the French lexicon"""
        df = LexiconFR.load(temp_fr_lexicon)
        
        # Check some common French words exist
        words = df[HeadersDF.ORTHO].str.lower().values
        # First 1000 rows should have basic words starting with 'a'
        assert len(words) > 0
        assert any(word.startswith('a') for word in words)
    
    def test_french_grammar_parsing(self, temp_fr_lexicon):
        """Test that grammar is correctly parsed and mapped"""
        df = LexiconFR.load(temp_fr_lexicon)
        
        # Check _grammar has expected values
        grammar_values = set(df[HeadersDF.GRAMMAR].unique())
        # Should have at least some grammar types
        assert len(grammar_values) > 0
        assert any(g in grammar_values for g in [Grammar.NOUN, Grammar.VERB, Grammar.ADJECTIVE, Grammar.AUXILIARY])
