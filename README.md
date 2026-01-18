# Riddle Game Collection

This project contains various word game implementations including Wordle, Semantle, and crossword puzzles. It includes tools for finding optimal opening word combinations using letter frequency analysis and integer linear programming.

## Setup

After cloning the repository, install the package in editable mode:

```bash
# Install dependencies and the package
uv sync

# Or alternatively
uv pip install -e .
```

This installs the `riddle` module, making it available to all scripts in the project.

## Best Opening Words

### French

| Word Length | Number of Words | Opening Words                        |
|-------------|-----------------|--------------------------------------|
| 4 | 4               | deca, flop, murs, vint               |
| 4 | 5               | bang, dupe, fric, thym, vols         |
| 5 | 3               | abces, lundi, rompt                  |
| 5 | 4               | clamp, hebdo, jurys, vingt           |
| 6 | 2               | craint, moules                       |
| 6 | 3               | dragon, mythes, public               |
| 6 | 4               | bijoux, champs, devint, frugal       |
| 7 | 2               | inculpe, motards                     |
| 7 | 3               | chomage, devants, publier            |
| 7 | 4               | abdomen, facheux, piquant, verglas   |
| 8 | 2               | chanteur, diplomes                   |
| 8 | 3               | bucheron, domptage, festival         |
| 9 | 2               | degauchir, longtemps                 |

### English

| Word Length | Number of Words | Opening Words |
|-------------|-----------------|---------------|
| 5 | 3 | duchy, slain, trope |
| 5 | 4 | blank, crest, dough, wimpy |

## Usage

### Running Games

```bash
# Wordle game
uv run src/wordle/main_wordle_game.py

# Semantle game
uv run src/semantle/main_semantle_game.py

# Crossword game
uv run src/cross_word/main_cross_words_game.py

# Clustering analysis
uv run src/riddle/main_cluster.py
```

### Finding Optimal Opening Words

```bash
# French, 5-letter words, 2 words
uv run src/wordle/main_wordle_opening.py french 5 2

# English, 5-letter words, 3 words
uv run src/wordle/main_wordle_opening.py english 5 3
```

### Running Tests

```bash
uv run pytest tests
```