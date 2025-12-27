import time
import numpy as np
from common import load_model, load_most_frequent_words


def run_game(model, available_words):
    secret_word = np.random.choice(available_words)
    print("A secret word has been chosen. Try to guess it!")
    attempts = 0
    observed: dict[str, tuple[int, float]] = {}
    while True:
        print()
        guess = input("Enter your guess: ").strip()
        if guess.lower() == '_':
            print(f"The secret word was: {secret_word}")
            break
        if guess not in available_words:
            print(f"Word '{guess}' not in the list. Please try again.")
            continue

        attempts += 1
        if guess == secret_word:
            print(f"Congratulations! You've guessed the secret word '{secret_word}' in {attempts} attempts.")
            break

        # Provide feedback based on similarity
        similarity = model.similarity(guess, secret_word)
        score = 100 * similarity
        if guess not in observed:
            observed[guess] = attempts, score

        attempt = observed[guess][0]

        current_score = f"{attempt} {guess}: {score:.2f}"


        # print  a sorted list of all observed words by similarity
        sorted_observed = sorted(observed.items(), key=lambda item: item[1][1], reverse=False)
        for word, att_score in sorted_observed:
            attempt, score = att_score
            print(f"{attempt} {word}: {score:.2f}")

        print("----")
        print(current_score)


def main():
    print("Loading model...")
    tick = time.time()
    model = load_model()
    tock = time.time()
    print(f"Model loaded in {tock - tick:.02f} seconds.")

    # words = ["roi", "reine", "banane", "pomme", "voiture", "camion", "avion", "bateau", "félin", "chat", "chien"]
    words = load_most_frequent_words()

    run_game(model, words)


if __name__ == "__main__":
    main()

