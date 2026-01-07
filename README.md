# Wordle Opening Strategy Results

This project finds optimal opening word combinations for Wordle-like games using letter frequency analysis and integer linear programming.

## Best Opening Words

### French

| Word Length | Number of Words | Opening Words              |
|-------------|-----------------|----------------------------|
| 4 | 4               | deca, flop, murs, vint     |
| 4 | 5               | bang, dupe, fric, thym, vols |
| 5 | 3               | abces, lundi, rompt        |
| 5 | 4               | clamp, hebdo, jurys, vingt |
| 6 | 2               | amours, client             |
| 6 | 3               | dragon, mythes, public     |

### English

| Word Length | Number of Words | Opening Words |
|-------------|-----------------|---------------|
| 5 | 3 | duchy, slain, trope |
| 5 | 4 | blank, crest, dough, wimpy |

## Usage

To find optimal opening words for a specific configuration
```bash
# French, 5-letter length, 2 words
uv run src/main_wordle_opening.py french 5 2
```