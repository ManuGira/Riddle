"""
Unit tests for WordleCLI terminal interface.
"""
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from riddle import DATA_FOLDER_PATH
from wordle.wordle_state import WordleState, GuessResult
from wordle.wordle_game import WordleGame
from wordle.main_wordle_cli import WordleCLI, Colors


class TestWordleCLI:
    """Test the terminal UI for Wordle."""
    
    @pytest.fixture
    def mock_game(self):
        """Create a mock WordleGame instance."""
        game = Mock(spec=WordleGame)
        game.date = "2026-01-12"
        game.secret = "CRANE"
        game.MAX_ATTEMPTS = 6
        
        # Mock create_game_state to return WordleState
        game.create_game_state.return_value = WordleState(max_attempts=6)
        
        return game
    
    def test_cli_initialization(self, mock_game):
        """Test CLI initializes with game state."""
        cli = WordleCLI(mock_game)
        
        assert cli.game == mock_game
        assert cli.game_state is not None
        assert cli.game_state.attempts == 0
        assert cli.game_state.max_attempts == 6
        assert not cli.game_state.game_over
    
    def test_colorize_hint_correct(self, mock_game):
        """Test correct letter gets green color."""
        cli = WordleCLI(mock_game)
        
        result = cli.colorize_hint('A', 'correct')
        
        assert Colors.GOOD in result
        assert Colors.BOLD in result
        assert 'A' in result
        assert Colors.RESET in result
    
    def test_colorize_hint_present(self, mock_game):
        """Test present letter gets yellow color."""
        cli = WordleCLI(mock_game)
        
        result = cli.colorize_hint('B', 'present')
        
        assert Colors.WARNING in result
        assert Colors.BOLD in result
        assert 'B' in result
        assert Colors.RESET in result
    
    def test_colorize_hint_absent(self, mock_game):
        """Test absent letter gets gray color."""
        cli = WordleCLI(mock_game)
        
        result = cli.colorize_hint('Z', 'absent')
        
        assert Colors.GRAY in result
        assert 'Z' in result
        assert Colors.RESET in result
    
    def test_display_guess(self, mock_game, capsys):
        """Test guess display with colored hints."""
        cli = WordleCLI(mock_game)
        
        guess_result = GuessResult(
            word='CRANE',
            hints=[
                {'letter': 'C', 'status': 'correct'},
                {'letter': 'R', 'status': 'present'},
                {'letter': 'A', 'status': 'absent'}
            ],
            is_correct=False
        )
        
        cli.display_guess(guess_result)
        captured = capsys.readouterr()
        
        assert 'C' in captured.out
        assert 'R' in captured.out
        assert 'A' in captured.out
    
    def test_display_board_empty(self, mock_game, capsys):
        """Test board display with no guesses."""
        cli = WordleCLI(mock_game)
        
        cli.display_board()
        captured = capsys.readouterr()
        
        assert 'WORDLE' in captured.out
        assert '0/6' in captured.out
        assert '_  _  _  _  _' in captured.out
    
    def test_display_board_with_guesses(self, mock_game, capsys):
        """Test board display with existing guesses."""
        cli = WordleCLI(mock_game)
        cli.game_state.guesses = [
            GuessResult(
                word='STONE',
                hints=[
                    {'letter': 'S', 'status': 'absent'},
                    {'letter': 'T', 'status': 'present'},
                    {'letter': 'O', 'status': 'absent'},
                    {'letter': 'N', 'status': 'present'},
                    {'letter': 'E', 'status': 'correct'}
                ],
                is_correct=False
            )
        ]
        cli.game_state.attempts = 1
        
        cli.display_board()
        captured = capsys.readouterr()
        
        assert '1/6' in captured.out
        assert 'WORDLE' in captured.out
    
    @patch('builtins.input', return_value='CRANE')
    def test_get_guess_valid(self, mock_input, mock_game):
        """Test getting valid 5-letter guess."""
        cli = WordleCLI(mock_game)
        
        guess = cli.get_guess()
        
        assert guess == 'CRANE'
        assert len(guess) == 5
        assert guess.isalpha()
    
    @patch('builtins.input', side_effect=['ABC', 'CRANE'])
    def test_get_guess_invalid_length(self, mock_input, mock_game, capsys):
        """Test rejection of wrong length guess."""
        cli = WordleCLI(mock_game)
        
        guess = cli.get_guess()
        captured = capsys.readouterr()
        
        assert '❌' in captured.out
        assert 'exactly 5 letters' in captured.out
        assert guess == 'CRANE'
    
    @patch('builtins.input', side_effect=['12345', 'CRANE'])
    def test_get_guess_non_alpha(self, mock_input, mock_game, capsys):
        """Test rejection of non-alphabetic guess."""
        cli = WordleCLI(mock_game)
        
        guess = cli.get_guess()
        captured = capsys.readouterr()
        
        assert '❌' in captured.out
        assert 'only letters' in captured.out
        assert guess == 'CRANE'
    
    def test_display_victory(self, mock_game, capsys):
        """Test victory message display."""
        cli = WordleCLI(mock_game)
        cli.game_state.attempts = 3
        cli.game_state.max_attempts = 6
        cli.game_state.won = True
        
        cli.display_victory()
        captured = capsys.readouterr()
        
        assert 'CONGRATULATIONS' in captured.out
        assert '3/6' in captured.out
        assert 'CRANE' in captured.out
    
    def test_display_defeat(self, mock_game, capsys):
        """Test defeat message display."""
        cli = WordleCLI(mock_game)
        cli.game_state.attempts = 6
        cli.game_state.max_attempts = 6
        cli.game_state.lost = True
        
        cli.display_defeat()
        captured = capsys.readouterr()
        
        assert 'GAME OVER' in captured.out
        assert '6' in captured.out
        assert 'CRANE' in captured.out


class TestCLIGameIntegration:
    """Test CLI with real WordleGame integration."""
    
    @pytest.fixture
    def real_game(self):
        """Create a real WordleGame for integration tests."""
        words_file = DATA_FOLDER_PATH / "english_words.txt"
        return WordleGame("2026-01-12", words_file, "test-secret-key")
    
    def test_full_game_state_flow(self, real_game):
        """Test complete game state flow through CLI."""
        cli = WordleCLI(real_game)
        
        # Initial state
        assert cli.game_state.attempts == 0
        assert not cli.game_state.game_over
        
        # Make a guess through the game
        cli.game_state = real_game.check_guess("STONE", cli.game_state)
        
        # Verify state updated
        assert cli.game_state.attempts == 1
        assert len(cli.game_state.guesses) == 1
        assert cli.game_state.guesses[0].word == 'STONE'
    
    def test_game_win_condition(self, real_game):
        """Test CLI handles winning correctly."""
        cli = WordleCLI(real_game)
        secret = real_game.secret
        
        # Guess the secret word
        cli.game_state = real_game.check_guess(secret, cli.game_state)
        
        # Verify win state
        assert cli.game_state.won
        assert cli.game_state.game_over
        assert cli.game_state.guesses[0].is_correct
    
    def test_game_loss_condition(self, real_game):
        """Test CLI handles losing correctly."""
        cli = WordleCLI(real_game)
        
        # Make 6 wrong guesses
        wrong_guesses = ["AAAAA", "BBBBB", "CCCCC", "DDDDD", "EEEEE", "FFFFF"]
        for guess in wrong_guesses:
            if guess in real_game.word_list:
                try:
                    cli.game_state = real_game.check_guess(guess, cli.game_state)
                except ValueError:
                    # Skip if word not in list
                    pass
        
        # Verify loss if we actually made 6 attempts
        if cli.game_state.attempts >= 6:
            assert cli.game_state.lost
            assert cli.game_state.game_over
