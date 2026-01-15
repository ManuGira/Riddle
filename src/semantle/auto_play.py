"""
Automated player that uses the assistant to play the semantic game automatically.
"""
import time
import numpy as np
from riddle.common import load_model, load_most_frequent_words, compute_heatmap_matrix
import semantle.main_assistant_semantic as mass
import semantle.main_semantle_game as mgame


def auto_play_game(game: mgame.SemanticGame, assistant: mass.GameAssistant, max_attempts=50, verbose=True):
    """
    Automatically play the game using the assistant's strategy.

    Args:
        model: Word2Vec model
        heatmap_matrix: Precomputed similarity matrix
        words: List of all available words
        secret_word: The target word to guess
        verbose: Whether to print progress
        max_attempts: Maximum number of attempts before giving up

    Returns:
        Tuple of (success, num_attempts, guess_history)
    """


    if verbose:
        print(f"\n{'='*60}")
        print(f"Starting new game. Secret word: {game.secret_word}")
        print(f"{'='*60}")

    next_suggestion = assistant.next_suggestion

    for attempt in range(1, max_attempts + 1):

        score, msg = game.play_turn(next_suggestion)
        score = round(score)
        if verbose:
            print(f"{attempt} '{next_suggestion}' → {score:.2f}")

        if game.game_on is False:
            if verbose:
                print(f"\n✅ SUCCESS: Guessed '{next_suggestion}' in {attempt} attempts")
            return True, attempt

        next_suggestion, msg = assistant.add_word_score(next_suggestion, score)


    if verbose:
        print(f"\n❌ FAILED: Could not guess '{game.secret_word}' in {max_attempts} attempts")
    return False, max_attempts


def run_multiple_games(model, heatmap_matrix, words, num_games=10, max_attempts=50, verbose=True):
    """
    Run multiple automated games and collect statistics.

    Args:
        model: Word2Vec model
        heatmap_matrix: Precomputed similarity matrix
        words: List of all available words
        num_games: Number of games to play
        max_attempts: Maximum attempts per game
        verbose: Whether to print detailed progress

    Returns:
        Dictionary with statistics
    """
    results = {
        'successes': 0,
        'failures': 0,
        'total_attempts': [],
        'successful_attempts': [],
        'secret_words': [],
        'game_details': []
    }

    print(f"\n{'='*60}")
    print(f"Running {num_games} automated games...")
    print(f"{'='*60}")

    for game_num in range(1, num_games + 1):
        # Pick a random secret word
        secret_word = np.random.choice(words)

        if verbose:
            print(f"\n\n{'#'*60}")
            print(f"GAME {game_num}/{num_games}")
            print(f"{'#'*60}")
        else:
            print(f"Game {game_num}/{num_games}: ", end='', flush=True)

        assistant = mass.GameAssistant(heatmap_matrix, words)
        game = mgame.SemanticGame(model, words)

        success, attempts  = auto_play_game(game, assistant, max_attempts, verbose)

        results['total_attempts'].append(attempts)
        results['secret_words'].append(secret_word)
        results['game_details'].append({
            'secret_word': secret_word,
            'success': success,
            'attempts': attempts,
        })

        if success:
            results['successes'] += 1
            results['successful_attempts'].append(attempts)
            if not verbose:
                print(f"✓ Success in {attempts} attempts")
        else:
            results['failures'] += 1
            if not verbose:
                print(f"✗ Failed")

    # Print summary statistics
    print(f"\n\n{'='*60}")
    print(f"SUMMARY STATISTICS")
    print(f"{'='*60}")
    print(f"Total games played: {num_games}")
    print(f"Successes: {results['successes']} ({results['successes']/num_games*100:.1f}%)")
    print(f"Failures: {results['failures']} ({results['failures']/num_games*100:.1f}%)")

    if results['successful_attempts']:
        avg_attempts = np.mean(results['successful_attempts'])
        min_attempts = np.min(results['successful_attempts'])
        max_attempts_success = np.max(results['successful_attempts'])
        print(f"\nSuccessful games statistics:")
        print(f"  Average attempts: {avg_attempts:.1f}")
        print(f"  Min attempts: {min_attempts}")
        print(f"  Max attempts: {max_attempts_success}")

    return results


def main():
    """Main entry point for automated playing."""
    # Configuration
    N = 3100  # Number of words to use
    num_games = 10  # Number of games to play
    max_attempts = 500  # Max attempts per game
    verbose = True  # Set to True for detailed output per game

    print("="*60)
    print("AUTOMATED SEMANTIC GAME PLAYER")
    print("="*60)

    # Load model for scoring (always needed)
    model = load_model()
    words = load_most_frequent_words(N, model)
    # words = ["roi", "reine", "banane", "pomme", "voiture", "camion", "avion", "bateau", "félin", "chat", "chien"]

    heatmap_matrix, words = mass.compute_heatmap_matrix_if_needed(words)

    # Run multiple games
    results = run_multiple_games(
        model, heatmap_matrix, words,
        num_games=num_games,
        max_attempts=max_attempts,
        verbose=verbose
    )

    # Optionally save results
    print("\nDone!")


if __name__ == "__main__":
    main()

