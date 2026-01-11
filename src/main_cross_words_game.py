import dataclasses
import enum
import numpy as np
import common as cmn
import coordinatus as co
from riddle import IRiddle

class Orientation(enum.Enum):
    HORIZONTAL = 'H'
    VERTICAL = 'V'

class CellState(enum.Enum):
    BLOCKED = 0
    FILLED = 1
    AVAILABLE = 2
    AVAILABLE_HORIZONTAL = 3
    AVAILABLE_VERTICAL = 4

@dataclasses.dataclass
class LetterCoord:
    pos_xy: co.Point
    orientation: Orientation
    char: str = ""

class WordCoord:
    def __init__(self, word: str, pos_xy: co.Point, orientation: Orientation):
        self.word = word
        self.orientation = orientation
        assert isinstance(pos_xy, co.Point), f"pos_xy must be a coordinatus Point, got {type(pos_xy)}"
        self.pos_xy = pos_xy

        # Set up local coordinate system for the word
        tx, ty = pos_xy.coords.round().astype(int)
        sy = 1
        angle_rad = 0.0
        if self.orientation == Orientation.VERTICAL:
            sy=-1
            angle_rad=np.pi/2

        self.local_frame = co.create_frame(None, tx=tx, ty=ty, angle_rad=angle_rad, sy=sy)


    def board_to_local_coordinates(self, board_pos_xy: tuple[int, int]) -> tuple[int, int]:
        """Convert global grid coordinates to local word coordinates."""
        pos = co.Point(board_pos_xy)
        pos = pos.relative_to(self.local_frame)
        local_pos_xy = pos.coords.round().astype(int).tolist()
        return local_pos_xy.tolist()

    def local_to_board_coordinates(self, local_pos_xy: tuple[int, int]) -> tuple[int, int]:
        """Convert local word coordinates to global grid coordinates."""
        pos = co.Point(local_pos_xy, frame=self.local_frame)
        pos = pos.to_absolute()
        board_pos_xy = pos.coords.round().astype(int).tolist()
        return board_pos_xy

    def __eq__(self, other: 'WordCoord'):
        if not isinstance(other, WordCoord):
            return NotImplemented
        return (self.word == other.word and
                self.pos_xy == other.pos_xy and
                self.orientation == other.orientation)

    def char_at_grid_pos(self, pos_xy: co.Point) -> tuple[CellState, str]:
        """Get character at given position if it exists in the word placement."""
        x, y = pos_xy.relative_to(self.local_frame).coords.round().astype(int)

        y_distance = abs(y)
        if x < 0:
            x_distance = -x
        elif x >= len(self.word):
            x_distance = x - len(self.word) + 1
        else:
            x_distance = 0
        distance = y_distance + x_distance
        
        if distance > 1:
            return CellState.AVAILABLE, ""
        
        if distance == 1:
            if y_distance == 0:
                return CellState.BLOCKED, ""

            match self.orientation:
                case Orientation.HORIZONTAL:
                    return CellState.AVAILABLE_VERTICAL, ""
                case Orientation.VERTICAL:
                    return CellState.AVAILABLE_HORIZONTAL, ""

        return CellState.FILLED, self.word[x]

    def letters(self) -> list[LetterCoord]:
        """Get all letters with their positions and orientations."""
        letters = []
        for idx, char in enumerate(self.word):
            letters.append(
                LetterCoord(
                    co.Point([idx, 0], self.local_frame).to_absolute(),
                    self.orientation,
                    char,
                ))

        return letters

    def get_pre_padding(self) -> LetterCoord:
        board_pos = co.Point((-1, 0), self.local_frame).to_absolute()
        return LetterCoord(board_pos, self.orientation, "0")

    def get_post_padding(self) -> LetterCoord:
        board_pos = co.Point((len(self.word), 0), self.local_frame).to_absolute()
        return LetterCoord(board_pos, self.orientation, "0")

        
    def find_cross_points(self, other_word: str) -> list['WordCoord']:
        """Find cross points between this word and another word."""
        cross_points = []
        other_orientation = Orientation.VERTICAL if self.orientation == Orientation.HORIZONTAL else Orientation.HORIZONTAL

        for i, char1 in enumerate(self.word):
            for j, char2 in enumerate(other_word):
                if char1 == char2:
                    board_pos = co.Point([i, -j], self.local_frame).to_absolute()
                    cross_points.append(WordCoord(other_word, board_pos, other_orientation))
        return cross_points
    
        
class CrossWordsBoard:
    def __init__(self):
        self.word_coords: list[WordCoord] = []
        self.revealed_placements: list[bool] = []

    def is_valid_placement(self, new_word: WordCoord) -> bool:
        """Check if a crossword placement is valid on the board."""

        letters = [new_word.get_pre_padding()] + new_word.letters() + [new_word.get_post_padding()]

        for letter in letters:
            for crossword in self.word_coords:
                crossword_state, crossword_char = crossword.char_at_grid_pos(letter.pos_xy)

                if crossword_state == CellState.BLOCKED:
                    return False

                if crossword_state == CellState.FILLED and crossword_char != letter.char:
                    return False

                if crossword_state == CellState.AVAILABLE_HORIZONTAL and letter.orientation != Orientation.HORIZONTAL:
                    return False

                if crossword_state == CellState.AVAILABLE_VERTICAL and letter.orientation != Orientation.VERTICAL:
                    return False

        return True

    def add_word(self, word: WordCoord) -> None:
        self.word_coords.append(word)
        self.revealed_placements.append(False)

    def reveal_word(self, word: str) -> None:
        for idx, placement in enumerate(self.word_coords):
            if placement.word == word:
                self.revealed_placements[idx] = True
        

    def compute_new_word_coordinates(self, word: str) -> list[WordCoord]:
        if len(self.word_coords) == 0:
            return [WordCoord(word, co.Point([0, 0]), Orientation.HORIZONTAL)]

        valid_crossword_positions: list[WordCoord] = []
        for crossword in self.word_coords:
            valid_crossword_positions += crossword.find_cross_points(word)

        # filter valid placements
        valid_crossword_positions = [cp for cp in valid_crossword_positions if self.is_valid_placement(cp)]
        return valid_crossword_positions


    def get_char(self, pos_xy: co.Point) -> str:
        """Get character at given position from any word placement."""
        for placement in self.word_coords:
            cellstate, char = placement.char_at_grid_pos(pos_xy)
            if cellstate == CellState.FILLED:
                return char
        return ""

    def compute_board_bounds(self) -> tuple[int, int, int, int]:
        """Compute the bounding box of the current board."""
        if not self.word_coords:
            return 0, 0, 0, 0

        letters = [letter for placement in self.word_coords for letter in placement.letters()]

        min_x = int(round(min(letter.pos_xy[0] for letter in letters)))
        max_x = int(round(max(letter.pos_xy[0] for letter in letters)))
        min_y = int(round(min(letter.pos_xy[1] for letter in letters)))
        max_y = int(round(max(letter.pos_xy[1] for letter in letters)))

        return min_x, max_x, min_y, max_y

    def render_revealed_board_txt(self) -> np.ndarray:
        """Display the current state of the board."""
        if not self.word_coords:
            print("Board is empty.")
            return np.array([[]])

        min_x, max_x, min_y, max_y = self.compute_board_bounds()

        board_frame = co.create_frame(None, tx=min_x, ty=min_y)
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        board_array = np.full((height, width), ".", dtype=str)

        letters = [letter for placement in self.word_coords for letter in placement.letters()]
        for letter in letters:
            pos_xy = letter.pos_xy.relative_to(board_frame)
            x, y = pos_xy.coords.round().astype(int)
            board_array[y, x] = letter.char

        return board_array

    def render_board_mask_bool(self) -> np.ndarray:
        if not self.word_coords:
            print("Board is empty.")
            return np.array([[]])

        min_x, max_x, min_y, max_y = self.compute_board_bounds()
        board_frame = co.create_frame(None, tx=min_x, ty=min_y)
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        board_mask = np.full((height, width), False, dtype=bool)
        for revealed, word in zip(self.revealed_placements, self.word_coords):
            if not revealed:
                continue
            for letter in word.letters():
                pos_xy = letter.pos_xy.relative_to(board_frame)
                x, y = pos_xy.coords.round().astype(int)
                board_mask[y, x] = True

        return board_mask

    def render_board_txt(self) -> np.ndarray:
        board_str = self.render_revealed_board_txt()
        board_mask = self.render_board_mask_bool()

        letters_to_mask = np.logical_and(board_str != ".", ~board_mask)
        board_str[letters_to_mask] = "+"
        return board_str

class IModel:
    def similarity(self, word1: str, word2: str) -> float:
        pass

class CrossWordsGame:
    def __init__(self, board: CrossWordsBoard, model: IModel, size: int):
        self.board = board
        self.model = model
        self.size = size

        sorted_words, similarity_map = self.load_words(self.model)
        self.root_word: str = sorted_words[0]
        self.sorted_words: list[str] = sorted_words
        self.similarity_map: dict[str, float] = similarity_map

        self.generate_game()


    @staticmethod
    def load_words(model: IModel) -> tuple[list[str], dict[str, float]]:
        # self.model_path = "frWac_non_lem_no_postag_no_phrase_200_cbow_cut100.bin"  # TODO: Update with actual path

        # Step 1: Load word2vec model
        # print("Loading word2vec model...")
        # model = cmn.load_model(model_path)

        print("Loading frequent words...")
        frequent_words = cmn.load_most_frequent_words(model=model)

        # filter out words shorter than 3 characters
        frequent_words: list[str] = [word for word in frequent_words if len(word) >= 3]

        # Choose a root word at random from the frequent words
        root_word: str = np.random.choice(frequent_words)

        # sort all words by their similarity to the root word
        print("Sorting words by similarity to root word:", root_word)
        similarity_map: dict[str, float] = {word: model.similarity(root_word, word) for word in frequent_words}

        sorted_words: list[str] = sorted(frequent_words, key=lambda w: similarity_map[w], reverse=True)
        return sorted_words, similarity_map

    def generate_game(self):
        placed_words = []
        while len(self.board.word_coords) < self.size:
            # find the first word in sorted_words that is not already on the board
            word = None
            candidate_word_coords: list[WordCoord] = []
            for candidate_word in self.sorted_words:
                if candidate_word not in placed_words :
                    word = candidate_word

                    # Compute candidate placements for the new word
                    candidate_word_coords = self.board.compute_new_word_coordinates(word)
                    print(f"Candidates for '{word}':")
                    for candidate in candidate_word_coords:
                        print("\t", candidate)
                    if len(candidate_word_coords) == 0:
                        print(f"No valid placements for '{word}'. Skipping.")
                        continue

                    break

            if candidate_word_coords:
                # Group by candidate duplicates. choose in priority candidates with most duplicates.
                # This favors placements that cross multiple words, making the game easier to solve
                candidate_count: dict[int, list[WordCoord]] = {}
                for candidate in candidate_word_coords:
                    count = sum(1 for other in candidate_word_coords if other == candidate)
                    if count not in candidate_count:
                        candidate_count[count] = []
                    candidate_count[count].append(candidate)

                    max_count = max(candidate_count.keys())
                    candidate_word_coords = candidate_count[max_count]

            new_crossword = np.random.choice(candidate_word_coords) if candidate_word_coords else None
            self.board.add_word(new_crossword)
            placed_words.append(word)

def run_game():
    game = CrossWordsGame(
        CrossWordsBoard(),
        cmn.load_model(),
        size=10,
    )

    # reveal the first word
    game.board.reveal_word(game.board.word_coords[0].word)
    # previous_board_str = None
    while True:
        board_str = game.board.render_board_txt()
        # if previous_board_str is None:
        #     previous_board_str = board_str

        print("Current board:")
        color_end = "\033[0m"
        for row_str in board_str:
            row = []
            for char in row_str:
                # blue bold default color
                color = "\033[94;1m"
                if char in "+.":
                    # light gray for hidden letters
                    color = "\033[90m"

                row.append(f"{color}{char}{color_end}")
            print(" ".join(row))

        user_word = input("Enter a word to reveal> ").strip()
        game.board.reveal_word(user_word)


def main():
    run_game()

if __name__ == "__main__":
    main()