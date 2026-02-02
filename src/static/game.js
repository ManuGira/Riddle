// Wordle Game Frontend
// Stateless architecture: all game state stored in JWT token

class WordleGame {
    constructor() {
        // Get base path from injected global variable (defaults to '' for root)
        this.basePath = window.GAME_BASE_PATH || '';
        // Create unique storage key for each game
        this.storageKey = this.basePath ? `${this.basePath.replace(/\//g, '_')}_token` : 'wordle_token';
        this.token = this.loadToken();
        this.gameState = null;
        this.gameInfo = null;
        this.isSubmitting = false;
        
        // Current guess stored as string (replaces input element)
        this.currentGuess = '';
        
        // DOM Elements
        this.board = document.getElementById('game-board');
        this.message = document.getElementById('message');
        this.dateDisplay = document.getElementById('date-display');
        this.attemptsDisplay = document.getElementById('attempts-display');
        this.keyboard = document.getElementById('keyboard');
        this.resetButton = document.getElementById('reset-button');
        this.infoButton = document.getElementById('info-button');
        this.infoModal = document.getElementById('info-modal');
        
        // Keyboard layout
        this.keyboardLayout = [
            ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
            ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
            ['ENTER', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', '⌫']
        ];
        
        this.letterStatus = {}; // Track letter statuses for keyboard coloring
        
        // Store bound resize handler reference for proper cleanup
        this.resizeHandler = null;
        
        this.init();
    }
    
    getApiUrl(endpoint) {
        // Construct full API URL using base path
        return `${this.basePath}${endpoint}`;
    }
    
    async init() {
        // Setup event listeners
        this.setupEventListeners();
        
        // Load game info
        await this.loadGameInfo();
        
        // Initialize board
        this.createBoard();
        
        // Create keyboard
        this.createKeyboard();
        
        // Check if we have a saved game state
        if (this.token) {
            await this.loadGameState();
        } else {
            this.updateDisplay();
        }
    }
    
    setupEventListeners() {
        // Reset button
        this.resetButton.addEventListener('click', () => this.resetGame());
        
        // Info button and modal
        this.infoButton.addEventListener('click', () => this.showModal());
        
        const closeButton = this.infoModal.querySelector('.close');
        closeButton.addEventListener('click', () => this.hideModal());
        
        window.addEventListener('click', (e) => {
            if (e.target === this.infoModal) {
                this.hideModal();
            }
        });
        
        // Physical keyboard support for desktop users
        document.addEventListener('keydown', (e) => {
            if (this.infoModal.style.display === 'block') return;
            if (this.gameState?.game_over) return;
            
            if (e.key === 'Enter') {
                e.preventDefault();
                this.submitGuess();
            } else if (e.key === 'Backspace') {
                e.preventDefault();
                this.currentGuess = this.currentGuess.slice(0, -1);
                this.updateCurrentRowTiles(this.currentGuess);
            } else if (/^[a-zA-Z]$/.test(e.key)) {
                const wordLength = this.gameInfo?.word_length || 5;
                if (this.currentGuess.length < wordLength) {
                    e.preventDefault();
                    this.currentGuess += e.key.toUpperCase();
                    this.updateCurrentRowTiles(this.currentGuess);
                }
            }
        });
    }
    
    async loadGameInfo() {
        try {
            const response = await fetch(this.getApiUrl('/api/info'));
            this.gameInfo = await response.json();
            this.dateDisplay.textContent = `📅 ${this.gameInfo.date}`;
        } catch (error) {
            console.error('Failed to load game info:', error);
            this.showMessage('❌ Failed to connect to server', 'error');
        }
    }
    
    createBoard() {
        this.board.innerHTML = '';
        const maxAttempts = this.gameInfo?.max_attempts || 6;
        const wordLength = this.gameInfo?.word_length || 5;
        
        const root = document.documentElement;
        
        // Use maximum tile size (62px) and gap (5px) - this defines the "max zoom"
        const maxTileSize = 62;
        const gap = 5;
        root.style.setProperty('--tile-size', `${maxTileSize}px`);
        root.style.setProperty('--gap', `${gap}px`);
        
        // Create the board rows and tiles
        for (let i = 0; i < maxAttempts; i++) {
            const row = document.createElement('div');
            row.className = 'board-row';
            row.dataset.row = i;
            
            for (let j = 0; j < wordLength; j++) {
                const tile = document.createElement('div');
                tile.className = 'tile';
                tile.dataset.col = j;
                row.appendChild(tile);
            }
            
            this.board.appendChild(row);
        }
        
        // Calculate and apply responsive scale
        this.updateBoardScale();
        
        // Remove previous resize listener if exists to prevent memory leaks
        if (this.resizeHandler) {
            window.removeEventListener('resize', this.resizeHandler);
        }
        
        // Re-calculate scale on window resize
        this.resizeHandler = () => this.updateBoardScale();
        window.addEventListener('resize', this.resizeHandler);
    }
    
    updateBoardScale() {
        // No-op: Layout is now handled by CSS constraints
        // This method is kept for compatibility but does nothing
        // CSS uses intrinsic sizing with aspect-ratio and viewport units
        return;
    }
    
    createKeyboard() {
        this.keyboard.innerHTML = '';
        
        this.keyboardLayout.forEach(row => {
            const keyRow = document.createElement('div');
            keyRow.className = 'keyboard-row';
            
            row.forEach(key => {
                const button = document.createElement('button');
                button.className = 'key';
                
                if (key === 'ENTER') {
                    button.classList.add('key-large');
                    button.textContent = 'ENTER';
                } else if (key === '⌫') {
                    button.classList.add('key-large');
                    button.textContent = '⌫';
                } else {
                    button.textContent = key;
                    button.dataset.letter = key;
                }
                
                button.addEventListener('click', () => this.handleKeyClick(key));
                keyRow.appendChild(button);
            });
            
            this.keyboard.appendChild(keyRow);
        });
    }
    
    handleKeyClick(key) {
        if (this.gameState?.game_over) return;
        
        const wordLength = this.gameInfo?.word_length || 5;
        
        if (key === 'ENTER') {
            this.submitGuess();
        } else if (key === '⌫') {
            this.currentGuess = this.currentGuess.slice(0, -1);
            this.updateCurrentRowTiles(this.currentGuess);
        } else {
            if (this.currentGuess.length < wordLength) {
                this.currentGuess += key;
                this.updateCurrentRowTiles(this.currentGuess);
            }
        }
    }
    
    updateCurrentRowTiles(text) {
        // Get current row from game state, or default to 0 for new games
        const currentRow = this.gameState?.attempts || 0;
        const row = this.board.querySelector(`[data-row="${currentRow}"]`);
        if (!row) return;
        
        const tiles = row.querySelectorAll('.tile');
        const wordLength = this.gameInfo?.word_length || 5;
        
        // Clear all tiles first
        tiles.forEach(tile => {
            tile.textContent = '';
            tile.classList.remove('filled');
        });
        
        // Fill tiles with current text
        for (let i = 0; i < Math.min(text.length, wordLength); i++) {
            tiles[i].textContent = text[i];
            tiles[i].classList.add('filled');
        }
    }
    
    async submitGuess() {
        if (this.isSubmitting) return;
        
        const guess = this.currentGuess.trim().toUpperCase();
        const wordLength = this.gameInfo?.word_length || 5;
        
        // Validation
        if (guess.length !== wordLength) {
            this.showMessage(`⚠️ Word must be ${wordLength} letters!`, 'warning');
            this.shakeCurrentRow();
            return;
        }
        
        if (!/^[A-Z]+$/.test(guess)) {
            this.showMessage('⚠️ Only letters allowed!', 'warning');
            this.shakeCurrentRow();
            return;
        }
        
        this.isSubmitting = true;
        
        try {
            const response = await fetch(this.getApiUrl('/api/guess'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    guess: guess,
                    token: this.token
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to submit guess');
            }
            
            const data = await response.json();
            
            // Update token and state
            this.token = data.token;
            this.saveToken(this.token);
            this.gameState = data.game_state;
            
            // Clear current guess
            this.currentGuess = '';
            
            // Update display
            this.updateDisplay();
            
            // Show message
            if (data.message) {
                const messageType = data.game_over ? 
                    (this.gameState.won ? 'success' : 'error') : 
                    'info';
                this.showMessage(data.message, messageType);
            }
            
        } catch (error) {
            console.error('Error submitting guess:', error);
            this.showMessage(`❌ ${error.message}`, 'error');
            this.shakeCurrentRow();
        } finally {
            this.isSubmitting = false;
        }
    }
    
    async loadGameState() {
        // Send empty guess to validate token and restore state
        // This doesn't consume an attempt
        try {
            const response = await fetch(this.getApiUrl('/api/guess'), {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    guess: "",
                    token: this.token
                })
            });
            
            const data = await response.json();
            
            // Update token and state
            this.token = data.token;
            this.saveToken(this.token);
            this.gameState = data.game_state;
            
            // Update display with restored state
            this.updateDisplay();
            
            // If game is over, show appropriate message
            if (this.gameState.game_over) {
                if (this.gameState.won) {
                    this.showMessage(`🎉 Game completed! You won in ${this.gameState.attempts} attempts!`, 'success');
                } else {
                    this.showMessage('💔 Game over! Try again tomorrow!', 'error');
                }
            }
            
        } catch (error) {
            console.error('Error loading game state:', error);
            // On error, just show empty board
            this.updateDisplay();
        }
    }
    
    async resetGame() {
        if (!confirm('Are you sure you want to reset the game? This will start over.')) {
            return;
        }
        
        try {
            const response = await fetch(this.getApiUrl('/api/reset'), {
                method: 'POST',
            });
            
            const data = await response.json();
            
            // Clear everything
            this.token = data.token;
            this.saveToken(this.token);
            this.gameState = null;
            this.letterStatus = {};
            this.currentGuess = '';
            
            // Re-initialize
            this.createBoard();
            this.createKeyboard();
            
            this.showMessage('🔄 Game reset! Good luck!', 'info');
            this.updateDisplay();
            
        } catch (error) {
            console.error('Error resetting game:', error);
            this.showMessage('❌ Failed to reset game', 'error');
        }
    }
    
    updateDisplay() {
        // Update attempts display
        const attempts = this.gameState?.attempts || 0;
        const maxAttempts = this.gameState?.max_attempts || this.gameInfo?.max_attempts || 6;
        this.attemptsDisplay.textContent = `📊 ${attempts}/${maxAttempts}`;
        
        // Update board with guesses
        if (this.gameState?.guesses) {
            this.gameState.guesses.forEach((guessResult, rowIndex) => {
                this.displayGuess(guessResult, rowIndex);
            });
        }
        
        // Update keyboard colors
        this.updateKeyboardColors();
    }
    
    displayGuess(guessResult, rowIndex) {
        const row = this.board.querySelector(`[data-row="${rowIndex}"]`);
        if (!row) return;
        
        const tiles = row.querySelectorAll('.tile');
        
        guessResult.hints.forEach((hint, colIndex) => {
            const tile = tiles[colIndex];
            tile.textContent = hint.letter;
            tile.classList.add(hint.status);
            
            // Animate tile flip
            tile.style.animationDelay = `${colIndex * 0.1}s`;
            tile.classList.add('flip');
            
            // Track letter status for keyboard
            const letter = hint.letter;
            const status = hint.status;
            
            // Priority: correct > present > absent
            if (!this.letterStatus[letter] || 
                (status === 'correct') ||
                (status === 'present' && this.letterStatus[letter] === 'absent')) {
                this.letterStatus[letter] = status;
            }
        });
    }
    
    updateKeyboardColors() {
        Object.keys(this.letterStatus).forEach(letter => {
            const key = this.keyboard.querySelector(`[data-letter="${letter}"]`);
            if (key) {
                const status = this.letterStatus[letter];
                key.classList.remove('correct', 'present', 'absent');
                key.classList.add(status);
            }
        });
    }
    
    showMessage(text, type = 'info') {
        this.message.textContent = text;
        this.message.className = `message ${type}`;
        this.message.classList.add('show');
        
        setTimeout(() => {
            this.message.classList.remove('show');
        }, 3000);
    }
    
    shakeCurrentRow() {
        // Get current row - defaults to 0 if gameState not yet loaded
        const currentRow = this.gameState?.attempts ?? 0;
        const row = this.board.querySelector(`[data-row="${currentRow}"]`);
        if (row) {
            row.classList.add('shake');
            setTimeout(() => {
                row.classList.remove('shake');
            }, 500);
        }
    }
    
    showModal() {
        this.infoModal.style.display = 'block';
    }
    
    hideModal() {
        this.infoModal.style.display = 'none';
    }
    
    // Token management (localStorage)
    loadToken() {
        const token = localStorage.getItem(this.storageKey);
        
        // Check if token is for today
        if (token) {
            try {
                // Decode JWT to check date (without verification)
                const payload = JSON.parse(atob(token.split('.')[1]));
                const tokenDate = payload.date;
                const today = new Date().toISOString().split('T')[0];
                
                if (tokenDate === today) {
                    return token;
                } else {
                    // Old token, clear it
                    localStorage.removeItem(this.storageKey);
                }
            } catch (e) {
                console.error('Error parsing token:', e);
                localStorage.removeItem(this.storageKey);
            }
        }
        
        return null;
    }
    
    saveToken(token) {
        if (token) {
            localStorage.setItem(this.storageKey, token);
        } else {
            localStorage.removeItem(this.storageKey);
        }
    }
}

// Initialize game when page loads
document.addEventListener('DOMContentLoaded', () => {
    new WordleGame();
});
