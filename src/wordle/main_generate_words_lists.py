
from riddle import DATA_FOLDER_PATH, Language
from riddle.lexicon_parser import LexiconFR, LexiconEN, HeadersDF, Grammar
import pandas as pd
from wordle import get_wordle_word_list_filepath, get_lexicon_path
from pathlib import Path


def generate_words_list(language: Language = Language.FR, word_length: int = 5, white_list: set[str] | None = None):
    """
    Generate a word list for Wordle from the OpenLexicon lexicon.
    The resulting word list will contain words of the specified length,
    without proper nouns, unknown grammar words, or weird characters.
    Accented characters will be replaced with their base characters.
    The word list will be saved as a tab-separated text file.
    :param language: Language of the lexicon (Language.FR or Language.EN)
    :param word_length: Desired length of the words in the word list
    :param white_list: Optional set of words to always include in the word list
    """

    # Example content of OpenLexicon_FR.tsv:
    """
    ortho	Lexique3__cgram	Lexique3__freqlemfilms2	Lexique3__islem
    a	NOM	81.36	1
    a	AUX	18559.22	0
    a	VER	13572.4	0
    a capella	ADV	0.04	1
    a cappella	ADV	0.04	1
    aa	NOM	0.01	1
    abaca	NOM	0.01	1
    abaissa	VER	4.93	0
    abaissai	VER	4.93	0
    abaissaient	VER	4.93	0
    """

    lexicon_path: Path = get_lexicon_path(language)
    output_filepath: Path = get_wordle_word_list_filepath(language, word_length)
    output_filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Select the appropriate lexicon class
    LexiconClass = LexiconFR if language == Language.FR else LexiconEN
    
    tick = pd.Timestamp.now()
    lexicon_df = LexiconClass.load(lexicon_path)
    print(f"Loaded lexicon with {len(lexicon_df)} entries")

    # remove words with weird characters: " '-_"
    weird_chars = set(" '-_")
    def has_weird_chars(word: str) -> bool:
        return any(char in weird_chars for char in word)
    mask = ~lexicon_df[HeadersDF.ORTHO].apply(has_weird_chars)
    lexicon_df = lexicon_df[mask]
    print(f"Filtered lexicon to {len(lexicon_df)} words without weird characters")

    # Filter out propper nouns and unknown grammar words
    invalid_grammars = {Grammar.PROPER_NOUN, Grammar.UNKNOWN, Grammar.OTHER}
    mask = ~lexicon_df[HeadersDF.GRAMMAR].isin(invalid_grammars)
    lexicon_df = lexicon_df[mask]

    # replace accented characters with corresponding base characters. Mapping in file "accent_to_base.json"
    import json
    accent_to_base_path = DATA_FOLDER_PATH / "accent_to_base.json"
    with open(accent_to_base_path, "r", encoding="utf-8") as f:
        accent_to_base = json.load(f)

    def replace_accents(word: str) -> str:
        return "".join(accent_to_base.get(char, char) for char in word)
    lexicon_df[HeadersDF.ORTHO] = lexicon_df[HeadersDF.ORTHO].apply(replace_accents)
    print("Replaced accented characters with base characters")

    # keep only words with the desired length
    lexicon_df = lexicon_df[lexicon_df[HeadersDF.ORTHO].str.len() == word_length]
    print(f"Filtered lexicon to {len(lexicon_df)} words with {word_length} letters")

    # remove duplicates words based on orthography, keep the one with highest frequency    
    lexicon_df = lexicon_df.sort_values(by=HeadersDF.FREQ, ascending=False)
    lexicon_df = lexicon_df.drop_duplicates(subset=[HeadersDF.ORTHO], keep='first')
    print(f"Filtered lexicon to {len(lexicon_df)} unique orthography")

    # extract ORTHO Column as word set
    words = set(lexicon_df[HeadersDF.ORTHO].tolist())

    # add white_list words if provided
    if white_list is not None:
        white_list = {w.lower() for w in white_list if len(w) == word_length and w.isalpha()}
        initial_count = len(words)
        words.update(white_list)
        print(f"Added {len(words) - initial_count} words from white_list")

    # Sort and save the word list
    print(f"Final word list contains {len(words)} words")
    words = list(sorted(words))

    # save the resulting word set as txt file
    with open(output_filepath, "w", encoding="utf-8") as f:
        for word in words:
            f.write(f"{word}\n")
    print(f"Saved word list to {output_filepath}")

    tock = pd.Timestamp.now()
    print(f"Loaded lexicon in {tock - tick}")


def main():
    # Generate French word lists
    print("=" * 60)
    print("Generating French word lists...")
    print("=" * 60)
    generate_words_list(Language.FR, 3)
    generate_words_list(Language.FR, 4)
    generate_words_list(Language.FR, 5)
    generate_words_list(Language.FR, 6)
    generate_words_list(Language.FR, 7)
    generate_words_list(Language.FR, 8)
    generate_words_list(Language.FR, 9)
    generate_words_list(Language.FR, 25)
    whites = {"intergouvernementalisation", "intergouvernementalisations"}
    generate_words_list(Language.FR, 26, white_list=whites)
    generate_words_list(Language.FR, 27, white_list=whites)

    # Generate English word lists
    print("\n" + "=" * 60)
    print("Generating English word lists...")
    print("=" * 60)
    generate_words_list(Language.EN, 3)
    generate_words_list(Language.EN, 4)

    # For english len 5, load a white list from the file "data/english_words.txt"
    white_list_path = DATA_FOLDER_PATH / "english_words.txt"
    with open(white_list_path, "r", encoding="utf-8") as f:
        white_list = {line.strip().lower() for line in f if line.strip()}
    generate_words_list(Language.EN, 5, white_list=white_list)

    generate_words_list(Language.EN, 6)
    generate_words_list(Language.EN, 7)
    generate_words_list(Language.EN, 8)
    generate_words_list(Language.EN, 9)

if __name__ == "__main__":
    main()