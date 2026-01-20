
from riddle import DATA_FOLDER_PATH
from riddle.lexicon_parser import LexiconFR, LexiconEN, Language, Grammar, HeadersDF
import pandas as pd


def main(language: Language = Language.FR, min_word_length: int = 3):
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
    output_filepath = output_folder_path / f"crossle_list_{language}_minL{min_word_length}_lem.txt"
    
    # Select the appropriate lexicon class
    LexiconClass = LexiconFR if language == Language.FR else LexiconEN
    
    tick = pd.Timestamp.now()
    lexicon_df = LexiconClass.load(lexicon_path)
    print(f"Loaded lexicon with {len(lexicon_df)} entries")

    # filter out non-lemmas
    if HeadersDF.IS_LEM in lexicon_df.columns:
        lexicon_df = lexicon_df[lexicon_df[HeadersDF.IS_LEM]]
        print(f"Filtered lexicon to {len(lexicon_df)} lemmas")
    else:
        print(f"Note: Lemma filtering not available for {language}, keeping all entries")

    # keep only content words: NOUN, VERB, ADJECTIVE, ADVERB
    content_grammars = {Grammar.NOUN, Grammar.VERB, Grammar.ADJECTIVE, Grammar.ADVERB}
    mask = lexicon_df[HeadersDF.GRAMMAR].isin(content_grammars)
    lexicon_df = lexicon_df[mask]
    print(f"Filtered lexicon to {len(lexicon_df)} content words (NOUN, VERB, ADJECTIVE, ADVERB)")

    # keep only words with the desired length
    lexicon_df = lexicon_df[lexicon_df[HeadersDF.ORTHO].str.len() >= min_word_length]
    print(f"Filtered lexicon to {len(lexicon_df)} words with at least {min_word_length} letters")

    # remove words with weird characters: " '-_"
    weird_chars = set(" '-_")
    def has_weird_chars(word: str) -> bool:
        return any(char in weird_chars for char in word)
    mask = ~lexicon_df[HeadersDF.ORTHO].apply(has_weird_chars)
    lexicon_df = lexicon_df[mask]
    print(f"Filtered lexicon to {len(lexicon_df)} words without weird characters")

    # remove duplicates based on orthography, keep the one with highest frequency
    lexicon_df = lexicon_df.sort_values(by=HeadersDF.FREQ, ascending=False)
    lexicon_df = lexicon_df.drop_duplicates(subset=[HeadersDF.ORTHO], keep='first')
    print(f"Filtered lexicon to {len(lexicon_df)} unique orthography")

    # save the resulting word list as txt file
    output_folder_path.mkdir(parents=True, exist_ok=True)
    lexicon_df[HeadersDF.ORTHO].to_csv(output_filepath, index=False, header=False, sep="\t", encoding="utf-8")
    print(f"Saved word list to {output_filepath}")

    tock = pd.Timestamp.now()
    print(f"Loaded lexicon in {tock - tick}")
    # print(lexicon_df.dtypes)

if __name__ == "__main__":
    # Generate for both languages
    print("=" * 60)
    print("Generating French word list...")
    print("=" * 60)
    main(Language.FR, 3)
    
    print("\n" + "=" * 60)
    print("Generating English word list...")
    print("=" * 60)
    main(Language.EN, 3)