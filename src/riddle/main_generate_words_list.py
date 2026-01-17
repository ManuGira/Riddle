import enum
import pandas as pd
from riddle import DATA_FOLDER_PATH


class CGram(enum.StrEnum):
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

class LexiColumn(enum.StrEnum):
    ORTHO = "ortho"
    PHON = "Lexique3__phon"
    LEMME = "Lexique3__lemme"
    CGRAM = "Lexique3__cgram"
    FREQ_LEM_FILMS2 = "Lexique3__freqlemfilms2"
    FREQ_FILMS2 = "Lexique3__freqfilms2"
    IS_LEM = "Lexique3__islem"
    NB_LETTRES = "Lexique3__nblettres"
    PU_ORTH = "Lexique3__puorth"
    PU_PHON = "Lexique3__puphon"
    NB_SYLL = "Lexique3__nbsyll"
    CGRAM_ORTHO = "Lexique3__cgramortho"

column_dtypes_map = {
    LexiColumn.ORTHO: str,
    LexiColumn.PHON: str,
    LexiColumn.LEMME: str,
    LexiColumn.CGRAM: str,
    LexiColumn.FREQ_LEM_FILMS2: float,
    LexiColumn.FREQ_FILMS2: float,
    LexiColumn.IS_LEM: bool,
    LexiColumn.NB_LETTRES: int,
    LexiColumn.PU_ORTH: int,
    LexiColumn.PU_PHON: int,
    LexiColumn.NB_SYLL: int,
    LexiColumn.CGRAM_ORTHO: str,
}

def main():
    lexicon_path = DATA_FOLDER_PATH / "french_OpenLexicon.tsv"
    output_folder_path = DATA_FOLDER_PATH / "word_lists"
    
    # Example content of french_OpenLexicon.tcv:
    """
    ortho	Lexique3__phon	Lexique3__lemme	Lexique3__cgram	Lexique3__freqlemfilms2	Lexique3__freqfilms2	Lexique3__islem	Lexique3__nblettres	Lexique3__puorth	Lexique3__puphon	Lexique3__nbsyll	Lexique3__cgramortho
    a	a	avoir	AUX	18559.22	6350.91	0	1	1	1	1	NOM,AUX,VER
    a	a	a	NOM	81.36	81.36	1	1	1	1	1	NOM,AUX,VER
    a	a	avoir	VER	13572.4	5498.34	0	1	1	1	1	NOM,AUX,VER
    a capella	akapEla	a capella	ADV	0.04	0.04	1	9	6	5	4	ADV
    a cappella	akapEla	a cappella	ADV	0.04	0.04	1	10	6	5	4	ADV
    a contrario	ak§tRaRjo	a contrario	ADV	0.0	0.0	1	11	4	5	4	ADV
    a fortiori	afORsjoRi	a fortiori	ADV	0.04	0.04	1	10	3	4	4	ADV
    a giorno	adZjORno	a giorno	ADV	0.0	0.0	1	8	3	4	3	ADV
    """
    tick = pd.Timestamp.now()
    lexicon_df = pd.read_csv(
        lexicon_path,
        sep="\t",
        dtype=column_dtypes_map,
        keep_default_na = False,  # do not convert "nan" to NaN
        # na_values = [],
    )
    print(f"Loaded lexicon with {len(lexicon_df)} entries")

    # filter out non-lemmas
    lexicon_df = lexicon_df[lexicon_df['Lexique3__islem']]
    print(f"Filtered lexicon to {len(lexicon_df)} lemmas")

    # map cgram strings to enum values
    lexicon_df[LexiColumn.CGRAM] = lexicon_df[LexiColumn.CGRAM].map(CGram)
    # keep only NOM, VER, ADJ, ADV
    cgrams = {CGram.NOM, CGram.VER, CGram.ADJ, CGram.ADV}
    mask = lexicon_df[LexiColumn.CGRAM].isin(cgrams)
    lexicon_df = lexicon_df[mask]
    print(f"Filtered lexicon to {len(lexicon_df)} content words (NOM, VER, ADJ, ADV)")

    # keep only words with more than 2 letters
    lexicon_df = lexicon_df[lexicon_df[LexiColumn.NB_LETTRES] > 3]
    print(f"Filtered lexicon to {len(lexicon_df)} words with more than 3 letters")

    # remove words with weird characters: " '-_"
    weird_chars = set(" '-_")
    def has_weird_chars(word: str) -> bool:
        return any(char in weird_chars for char in word)
    mask = ~lexicon_df[LexiColumn.ORTHO].apply(has_weird_chars)
    lexicon_df = lexicon_df[mask]
    print(f"Filtered lexicon to {len(lexicon_df)} words without weird characters")

    # remove duplicates based on lemma, keep the one with highest frequency
    lexicon_df = lexicon_df.sort_values(by=LexiColumn.FREQ_LEM_FILMS2, ascending=False)
    lexicon_df = lexicon_df.drop_duplicates(subset=[LexiColumn.LEMME], keep='first')
    print(f"Filtered lexicon to {len(lexicon_df)} unique lemmas")

    # save the resulting word list as txt file
    output_folder_path.mkdir(parents=True, exist_ok=True)
    output_path = output_folder_path / "french_word_list.txt"
    lexicon_df[LexiColumn.ORTHO].to_csv(output_path, index=False, header=False, sep="\t", encoding="utf-8")
    print(f"Saved word list to {output_path}")


    tock = pd.Timestamp.now()
    print(f"Loaded lexicon in {tock - tick}")
    # print(lexicon_df.dtypes)


if __name__ == "__main__":
    main()