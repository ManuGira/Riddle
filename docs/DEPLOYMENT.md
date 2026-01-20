# Deploying Wordle Game to the Internet

## Option 1: Render.com (RECOMMENDED - FREE)

### Prerequisites
- GitHub account
- Git installed
- `uv.lock` file (run `uv sync` locally to generate if missing)

### Steps

1. **Generate uv.lock file** (if not already present)
   ```bash
   cd D:\DataEmmanuel\Programmation\Riddle
   uv sync
   ```
   This creates a `uv.lock` file that Render will use for fast, reproducible builds.

2. **Push your code to GitHub**
   ```bash
   cd D:\DataEmmanuel\Programmation\Riddle
   git init
   git add .
   git commit -m "Initial commit - Wordle game"
   git remote add origin https://github.com/YOUR_USERNAME/riddle-game.git
   git push -u origin main
   ```

2. **Sign up on Render.com**
   - Go to https://render.com
   - **Create a new Web Service**
      - Click "New +" → "Web Service"
      - Enter URL of your "Riddle" github repository (if repo is private, connect Render to GitHub)
      - Set build command: `uv sync --frozen --no-dev && uv cache prune --ci`
      - Set start command: `uv run --no-dev src/wordle/main_wordle_server.py`
      - Add environment variables:
         - **PORT**: `10000` (This is required by Render)
         - **SECRET_KEY**: Choose a secure random string. 
   ```powershell
   # PowerShell
   uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
  
   ⚠️ **Never commit this key to Git!** It stays only in Render's dashboard.

4. **Deploy**
   - Service will auto-deploy after adding SECRET_KEY
   - Wait 2-3 minutes for deployment
   - Your game will be live at: `https://riddle-XXXX.onrender.com`
   
   **Note**: Render detects `uv.lock` and automatically uses `uv` for faster builds!

### Cost
- **FREE**: 750 hours/month
- Spins down after 15 min of inactivity
- First load takes ~30 seconds (cold start)
- **Faster builds** with uv (~30s vs ~2min with pip)
