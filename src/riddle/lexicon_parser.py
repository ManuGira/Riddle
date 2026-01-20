import dataclasses
import enum
from abc import ABC, abstractmethod
from typing import ClassVar


class Grammar(enum.StrEnum):
    """Common grammar categories across French and English lexicons."""
    NOUN = "NOUN"
    PROPER_NOUN = "PROPER_NOUN"  # Nom propre - proper nouns like "Charles", "America"
    VERB = "VERB"
    ADJECTIVE = "ADJECTIVE"
    ADVERB = "ADVERB"
    ARTICLE = "ARTICLE"
    PRONOUN = "PRONOUN"
    PREPOSITION = "PREPOSITION"
    CONJUNCTION = "CONJUNCTION"
    AUXILIARY = "AUXILIARY"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"

@dataclasses.dataclass
class HeadersTXT:
    ORTHO: str
    GRAMMAR_TXT: str
    FREQ: str
    LEMME: str
    IS_LEM: str

class HeadersDF:
    """Standard column names for lexicon dataframes."""
    ORTHO = "ortho"
    LEMME = "lemme"
    GRAMMAR_TXT = "grammar_txt"
    FREQ = "freq"
    IS_LEM = "is_lem"
    GRAMMAR = "grammar"

# Detect proper nouns: words starting with capital letter that are nouns
def is_proper_noun(row):
    word = row[HeadersDF.ORTHO]
    return word and word[0].isupper()

class Lexicon(ABC):
    """Abstract base class for lexicon implementations."""
    
    headers: ClassVar[HeadersTXT]
    txt_column_dtypes_map: ClassVar[dict[str, type]]
    
    @staticmethod
    @abstractmethod
    def to_common_grammar(grammar) -> Grammar:
        """Map language-specific grammar to common grammar categories."""
        pass
    
    @staticmethod
    @abstractmethod
    def parse_grammar(grammar_str: str):
        """Parse grammar string from lexicon file."""
        pass
    
    @staticmethod
    @abstractmethod
    def load(filepath):
        """Load lexicon from file and return a DataFrame with parsed columns."""
        pass

class LexiconFR(Lexicon):
    class GrammarFR(enum.StrEnum):
        a = "a"
        ADJ = "ADJ"
        ADJ_dem = "ADJ:dem"
        ADJ_ind = "ADJ:ind"
        ADJ_int = "ADJ:int"
        ADJ_num = "ADJ:num"
        ADJ_pos = "ADJ:pos"
        ADV = "ADV"
        ART_def = "ART:def"
        ART_ind = "ART:ind"
        AUX = "AUX"  # auxiliary verb (être, avoir et toutes leurs formes conjuguées)
        CON = "CON"
        LIA = "LIA"
        NOM = "NOM"
        ONO = "ONO"
        PRO_dem = "PRO:dem"
        PRO_ind = "PRO:ind"
        PRO_int = "PRO:int"
        PRO_per = "PRO:per"
        PRO_pos = "PRO:pos"
        PRO_rel = "PRO:rel"
        PRE = "PRE"
        VER = "VER"
        NONE = ""

    headers = HeadersTXT(
        ORTHO = "ortho",
        LEMME = "Lexique3__lemme",
        GRAMMAR_TXT = "Lexique3__cgram",
        FREQ = "Lexique3__freqlemfilms2",
        IS_LEM = "Lexique3__islem",
    )        

    txt_column_dtypes_map = {
        headers.ORTHO: str,
        headers.LEMME: str,
        headers.GRAMMAR_TXT: str,
        headers.FREQ: float,
        headers.IS_LEM: bool,
    }

    @staticmethod
    def to_common_grammar(grammar: "LexiconFR.GrammarFR") -> Grammar:
        """Map French grammar to common grammar categories."""
        mapping = {
            LexiconFR.GrammarFR.NOM: Grammar.NOUN,
            LexiconFR.GrammarFR.VER: Grammar.VERB,
            LexiconFR.GrammarFR.ADJ: Grammar.ADJECTIVE,
            LexiconFR.GrammarFR.ADJ_dem: Grammar.ADJECTIVE,
            LexiconFR.GrammarFR.ADJ_ind: Grammar.ADJECTIVE,
            LexiconFR.GrammarFR.ADJ_int: Grammar.ADJECTIVE,
            LexiconFR.GrammarFR.ADJ_num: Grammar.ADJECTIVE,
            LexiconFR.GrammarFR.ADJ_pos: Grammar.ADJECTIVE,
            LexiconFR.GrammarFR.ADV: Grammar.ADVERB,
            LexiconFR.GrammarFR.ART_def: Grammar.ARTICLE,
            LexiconFR.GrammarFR.ART_ind: Grammar.ARTICLE,
            LexiconFR.GrammarFR.PRO_dem: Grammar.PRONOUN,
            LexiconFR.GrammarFR.PRO_ind: Grammar.PRONOUN,
            LexiconFR.GrammarFR.PRO_int: Grammar.PRONOUN,
            LexiconFR.GrammarFR.PRO_per: Grammar.PRONOUN,
            LexiconFR.GrammarFR.PRO_pos: Grammar.PRONOUN,
            LexiconFR.GrammarFR.PRO_rel: Grammar.PRONOUN,
            LexiconFR.GrammarFR.PRE: Grammar.PREPOSITION,
            LexiconFR.GrammarFR.CON: Grammar.CONJUNCTION,
            LexiconFR.GrammarFR.AUX: Grammar.AUXILIARY,
            LexiconFR.GrammarFR.LIA: Grammar.OTHER,
            LexiconFR.GrammarFR.ONO: Grammar.OTHER,
            LexiconFR.GrammarFR.a: Grammar.OTHER,
            LexiconFR.GrammarFR.NONE: Grammar.UNKNOWN,
        }
        return mapping.get(grammar, Grammar.UNKNOWN)
    
    @staticmethod
    def parse_grammar(grammar_str: str):
        """Parse French grammar string, keeping only the first grammar."""
        if not grammar_str or grammar_str.strip() == "":
            return LexiconFR.GrammarFR.NONE

        return LexiconFR.GrammarFR(grammar_str.strip())

    
    @staticmethod
    def load(filepath):
        import pandas as pd

        # Create dtype map
        dtype_map = LexiconFR.txt_column_dtypes_map.copy()
        
        lexicon_df = pd.read_csv(
            filepath,
            sep="\t",
            dtype=dtype_map,
            keep_default_na = False,  # do not convert "nan" to NaN
        )
        
        # Rename columns to standard names
        column_mapping = {
            LexiconFR.headers.ORTHO: HeadersDF.ORTHO,
            LexiconFR.headers.LEMME: HeadersDF.LEMME,
            LexiconFR.headers.GRAMMAR_TXT: HeadersDF.GRAMMAR_TXT,
            LexiconFR.headers.FREQ: HeadersDF.FREQ,
            LexiconFR.headers.IS_LEM: HeadersDF.IS_LEM,
        }
        lexicon_df = lexicon_df.rename(columns=column_mapping)
        
        # Add common grammar column
        lexicon_df[HeadersDF.GRAMMAR] = lexicon_df[HeadersDF.GRAMMAR_TXT].apply(LexiconFR.parse_grammar).apply(LexiconFR.to_common_grammar)
        
       
        # Detect proper nouns: words starting with capital letter that are nouns
        mask = lexicon_df.apply(is_proper_noun, axis=1)
        lexicon_df.loc[mask, HeadersDF.GRAMMAR] = Grammar.PROPER_NOUN

        return lexicon_df

class LexiconEN(Lexicon):
    class GrammarEN(enum.StrEnum):
        NOUN = "NN"  # Noun
        VERB = "VB"  # Verb
        ADJ = "JJ"   # Adjective
        ADV = "RB"   # Adverb
        MINOR = "minor"  # Minor category
        ENCL = "encl"    # Enclitic, e.g., "'s", "n't"
        NONE = ""

    headers = HeadersTXT(
        ORTHO = "ortho",
        GRAMMAR_TXT = "English_Lexicon_Project__POS",
        FREQ = "English_Lexicon_Project__SUBTLWF",
        IS_LEM = "",  # not present in EN lexicon
        LEMME = "",  # not present in EN lexicon
    )

    txt_column_dtypes_map = {
        headers.ORTHO: str,
        headers.GRAMMAR_TXT: str,
        headers.FREQ: float,
        # LEMME not present in EN lexicon
        # IS_LEM not present in EN lexicon
    }

    @staticmethod
    def to_common_grammar(grammar: "LexiconEN.GrammarEN") -> Grammar:
        """Map English grammar to common grammar categories."""
        mapping = {
            LexiconEN.GrammarEN.NOUN: Grammar.NOUN,
            LexiconEN.GrammarEN.VERB: Grammar.VERB,
            LexiconEN.GrammarEN.ADJ: Grammar.ADJECTIVE,
            LexiconEN.GrammarEN.ADV: Grammar.ADVERB,
            LexiconEN.GrammarEN.MINOR: Grammar.OTHER,
            LexiconEN.GrammarEN.ENCL: Grammar.OTHER,
            LexiconEN.GrammarEN.NONE: Grammar.UNKNOWN,
        }
        return mapping.get(grammar, Grammar.UNKNOWN)

    @staticmethod
    def parse_grammar(grammar_str):
        """Parse pipe-separated grammar string, keeping only the first grammar."""
        if not grammar_str or grammar_str.strip() == "":
            return LexiconEN.GrammarEN.NONE

        try:
            grams: list[LexiconEN.GrammarEN] = [LexiconEN.GrammarEN(gram) for gram in grammar_str.split("|")]
            if len(grams) == 1:
                return grams[0]
            for gram in LexiconEN.GrammarEN:
                if gram in grams:
                    return gram
        except ValueError as e:
            raise ValueError(f"Could not parse grammar string: '{grammar_str}'") from e

        raise ValueError(f"Could not parse grammar string: '{grammar_str}'")
    
    @staticmethod
    def load(filepath):
        import pandas as pd

        # Define converters to handle comma-separated numbers
        def parse_freq(value):
            if not value or value.strip() == "":
                return None
            return float(value.replace(",", ""))
        
        converters = {
            LexiconEN.headers.FREQ: parse_freq
        }
        
        # Create dtype map without the FREQ column (handled by converter)
        dtype_map = {k: v for k, v in LexiconEN.txt_column_dtypes_map.items() 
                     if k != LexiconEN.headers.FREQ}
        
        lexicon_df = pd.read_csv(
            filepath,
            sep="\t",
            dtype=dtype_map,
            converters=converters,
            keep_default_na = False,  # do not convert "nan" to NaN
        )
        
        # Rename columns to standard names
        column_mapping = {
            LexiconEN.headers.ORTHO: HeadersDF.ORTHO,
            LexiconEN.headers.GRAMMAR_TXT: HeadersDF.GRAMMAR_TXT,
            LexiconEN.headers.FREQ: HeadersDF.FREQ,
        }
        lexicon_df = lexicon_df.rename(columns=column_mapping)
        
        # print first rows for debugging


        # Add common grammar column
        lexicon_df[HeadersDF.GRAMMAR] = lexicon_df[HeadersDF.GRAMMAR_TXT].apply(LexiconEN.parse_grammar).apply(LexiconEN.to_common_grammar)
        
        # Detect proper nouns: words starting with capital letter that are nouns
        mask = lexicon_df.apply(is_proper_noun, axis=1)
        lexicon_df.loc[mask, HeadersDF.GRAMMAR] = Grammar.PROPER_NOUN

        return lexicon_df


def demo():
    """Demo loading lexicon files."""
    import time
    from riddle import DATA_FOLDER_PATH

    tick = time.time()
    lexicon_path = DATA_FOLDER_PATH / "OpenLexicon_FR.tsv"
    df = LexiconFR.load(lexicon_path)
    print(df.head())
    tock = time.time()
    print(f"Loading took {tock - tick:.2f} seconds")
    print()

    tick = time.time()
    lexicon_path = DATA_FOLDER_PATH / "OpenLexicon_EN.tsv"
    df = LexiconEN.load(lexicon_path)
    print(df.head())
    tock = time.time()
    print(f"Loading took {tock - tick:.2f} seconds")

   

if __name__ == "__main__":
    demo()