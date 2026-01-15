import time
import numpy as np
from riddle.common import load_model, load_most_frequent_words


class SemanticGame:
    def __init__(self, model, available_words):
        self.model = model
        self.available_words = available_words
        self.secret_word = np.random.choice(available_words)
        self.attempts = 0
        self.observed: dict[str, tuple[int, float]] = {}
        self.game_on = True

    def play_turn(self, guess) -> tuple[float, str]:
        if guess not in self.available_words:
            msg = f"Word '{guess}' not in the list. Please try again."
            return None, msg

        # Provide feedback based on similarity
        similarity = self.model.similarity(guess, self.secret_word)
        score = 100 * similarity
        if guess not in self.observed:
            self.observed[guess] = self.attempts, score

        attempt = self.observed[guess][0]

        score_msg = f"{attempt} {guess}: {score:.2f}"
        msg = ""

        self.attempts += 1
        if guess == self.secret_word:
            self.game_on = False
            msg += f"\nCongratulations! You've guessed the secret word '{self.secret_word}' in {self.attempts} attempts."
            return score, msg

        # print a sorted list of all observed words by similarity
        sorted_observed = sorted(self.observed.items(), key=lambda item: item[1][1], reverse=False)
        for word_, att_score_ in sorted_observed:
            attempt_, score_ = att_score_
            msg += f"\n{attempt_} {word_}: {score_:.2f}"

        msg += f"\n----"
        msg += f"current_score"
        msg += f"\n{score_msg}"
        return score, msg

    def run_interactive(self):
        print("A secret word has been chosen. Try to guess it!")
        while self.game_on:
            score, msg = self.play_turn(input("Enter your guess: ").strip())
            print(msg)

def main():
    print("Loading model...")
    model = load_model()

    # words = ["roi", "reine", "banane", "pomme", "voiture", "camion", "avion", "bateau", "félin", "chat", "chien"]
    words = load_most_frequent_words(3100, model)

    game = SemanticGame(model, words)
    game.run_interactive()


if __name__ == "__main__":
    main()

