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

<table>
<thead>
<tr>
<th>Word Length</th>
<th>Number of Words</th>
<th>Opening Words</th>
</tr>
</thead>
<tbody>
<tr style="background-color: #FFFFFF;">
<td>3</td>
<td>5</td>
<td>but - foc - lap - mir - nes</td>
</tr>
<tr style="background-color: #F5F5F5;">
<td>4</td>
<td>4</td>
<td>buts - fiel - marc - pond</td>
</tr>
<tr style="background-color: #F5F5F5;">
<td>4</td>
<td>5</td>
<td>bang - dupe - fric - thym - vols</td>
</tr>
<tr style="background-color: #F5F5F5;">
<td>4</td>
<td>5</td>
<td>bock, gent, hard, plum, vifs</td>
</tr>
<tr style="background-color: #FFFFFF;">
<td>5</td>
<td>3</td>
<td>abces - lundi - rompt</td>
</tr>
<tr style="background-color: #FFFFFF;">
<td>5</td>
<td>4</td>
<td>clamp - hebdo - jurys - vingt</td>
</tr>
<tr style="background-color: #F5F5F5;">
<td>6</td>
<td>2</td>
<td>craint - moules</td>
</tr>
<tr style="background-color: #F5F5F5;">
<td>6</td>
<td>3</td>
<td>dragon - mythes - public</td>
</tr>
<tr style="background-color: #F5F5F5;">
<td>6</td>
<td>4</td>
<td>bijoux - champs - devint - frugal</td>
</tr>
<tr style="background-color: #FFFFFF;">
<td>7</td>
<td>2</td>
<td>inculpe - motards</td>
</tr>
<tr style="background-color: #FFFFFF;">
<td>7</td>
<td>3</td>
<td>chomage - devants - publier</td>
</tr>
<tr style="background-color: #FFFFFF;">
<td>7</td>
<td>4</td>
<td>abdomen - facheux - piquant - verglas</td>
</tr>
<tr style="background-color: #F5F5F5;">
<td>8</td>
<td>2</td>
<td>chanteur - diplomes</td>
</tr>
<tr style="background-color: #F5F5F5;">
<td>8</td>
<td>3</td>
<td>bucheron - domptage - festival</td>
</tr>
<tr style="background-color: #FFFFFF;">
<td>9</td>
<td>2</td>
<td>degauchir - longtemps</td>
</tr>
</tbody>
</table>

### English

<table>
<thead>
<tr>
<th>Word Length</th>
<th>Number of Words</th>
<th>Opening Words</th>
</tr>
</thead>
<tbody>
<tr style="background-color: #FFFFFF;">
<td>3</td>
<td>4</td>
<td>bet - dig - oar - pun</td>
</tr>
<tr style="background-color: #FFFFFF;">
<td>3</td>
<td>5</td>
<td>bed - out - ran - spy - wig</td>
</tr>
<tr style="background-color: #F5F5F5;">
<td>4</td>
<td>3</td>
<td>dare - punt - soil</td>
</tr>
<tr style="background-color: #F5F5F5;">
<td>4</td>
<td>4</td>
<td>ache - born - dump - silt</td>
</tr>
<tr style="background-color: #F5F5F5;">
<td>4</td>
<td>5</td>
<td>bums, fern, gold, pack, with</td>
</tr>
<tr style="background-color: #FFFFFF;">
<td>5</td>
<td>3</td>
<td>duchy - slain - trope</td>
</tr>
<tr style="background-color: #FFFFFF;">
<td>5</td>
<td>4</td>
<td>blank - crest - dough - wimpy</td>
</tr>
<tr style="background-color: #F5F5F5;">
<td>6</td>
<td>3</td>
<td>cymbal - gopher - nudist</td>
</tr>
<tr style="background-color: #FFFFFF;">
<td>7</td>
<td>2</td>
<td>closeup - trading</td>
</tr>
<tr style="background-color: #F5F5F5;">
<td>8</td>
<td>2</td>
<td>chapters - moulding</td>
</tr>
<tr style="background-color: #FFFFFF;">
<td>9</td>
<td>2</td>
<td>combating - upholders</td>
</tr>
</tbody>
</table>

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