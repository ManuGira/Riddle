
from riddle import DATA_FOLDER_PATH
from riddle.lexicon_parser import LexiconFR, LexiconEN, Language, HeadersDF, Grammar
import pandas as pd


def main(language: Language = Language.FR, word_length: int = 5):
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

    lexicon_path = DATA_FOLDER_PATH / f"OpenLexicon_{language}.tsv"
    output_folder_path = DATA_FOLDER_PATH / "words_lists"
    output_folder_path.mkdir(parents=True, exist_ok=True)
    output_filepath = output_folder_path / f"wordle_list_{language}_L{word_length}_base.txt"
    
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

    # sort words alphabetically
    lexicon_df = lexicon_df.sort_values(by=HeadersDF.ORTHO)

    # save the resulting word list as txt file
    output_folder_path.mkdir(parents=True, exist_ok=True)
    lexicon_df[HeadersDF.ORTHO].to_csv(output_filepath, index=False, header=False, sep="\t", encoding="utf-8")
    print(f"Saved word list to {output_filepath}")

    tock = pd.Timestamp.now()
    print(f"Loaded lexicon in {tock - tick}")


if __name__ == "__main__":
    # Generate French word lists
    print("=" * 60)
    print("Generating French word lists...")
    print("=" * 60)
    main(Language.FR, 5)
    main(Language.FR, 6)
    main(Language.FR, 7)
    main(Language.FR, 8)
    main(Language.FR, 9)
    
    # Generate English word lists
    print("\n" + "=" * 60)
    print("Generating English word lists...")
    print("=" * 60)
    main(Language.EN, 5)
    main(Language.EN, 6)
    main(Language.EN, 7)
    main(Language.EN, 8)
    main(Language.EN, 9)