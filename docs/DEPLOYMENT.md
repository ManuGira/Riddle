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
   - Sign up with your GitHub account

3. **Create a new Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select your "riddle-game" repository
   - Render will auto-detect the `render.yaml` file

4. **Set SECRET_KEY Environment Variable** (IMPORTANT!)
   - After creating the service, go to **Environment** tab
   - Click "Add Environment Variable"
   - **Name**: `SECRET_KEY`
   - **Value**: Generate a random string (see below)
   - Click "Save Changes"
   
   **Generate a secure SECRET_KEY:**
   ```bash
   # PowerShell
   -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
   
   # Or Python
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   
   ⚠️ **Never commit this key to Git!** It stays only in Render's dashboard.

5. **Deploy**
   - Service will auto-deploy after adding SECRET_KEY
   - Wait 2-3 minutes for deployment
   - Your game will be live at: `https://wordle-game-XXXX.onrender.com`
   
   **Note**: Render detects `uv.lock` and automatically uses `uv` for faster builds!

### Cost
- **FREE**: 750 hours/month
- Spins down after 15 min of inactivity
- First load takes ~30 seconds (cold start)
- **Faster builds** with uv (~30s vs ~2min with pip)

---

## Option 2: Railway.app (SIMPLE - $5/month)

1. **Push code to GitHub** (same as above)

2. **Sign up on Railway**
   - Go to https://railway.app
   - Sign up with GitHub

3. **Deploy**
   - Click "New Project" → "Deploy from GitHub"
   - Select your repository
   - Railway auto-detects Python
   - Add environment variable: `SECRET_KEY` (generate random string)

4. **Generate Domain**
   - Go to Settings → Generate Domain
   - Your game is live!

### Cost
- $5/month flat rate
- Always running (no cold starts)
- Better for consistent availability

---

## Option 3: Fly.io (FREE/CHEAP)

1. **Install Fly CLI**
   ```bash
   pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **Login**
   ```bash
   fly auth login
   ```

3. **Create fly.toml** (see below)

4. **Deploy**
   ```bash
   fly launch
   fly deploy
   ```

### Cost
- FREE: 3 shared-cpu-1x VMs + 3GB storage
- ~$0-3/month for a small game

---

## Generating SECRET_KEY

**IMPORTANT**: Never commit your SECRET_KEY to Git!

Generate a secure random key:
```bash
# PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Or use Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Where to store SECRET_KEY:**
- ✅ Render Dashboard → Environment Variables
- ✅ Railway Dashboard → Variables tab
- ✅ Fly.io → `fly secrets set SECRET_KEY=<value>`
- ✅ Local `.env` file (add to .gitignore)
- ❌ NEVER in render.yaml, .py files, or any committed code

---

## Security Best Practices

1. **SECRET_KEY stays secret**: Only set in platform dashboards, never in code
2. **Different keys per environment**: Use different SECRET_KEY for dev/prod
3. **Check .gitignore**: Ensure `.env`, `secrets.txt`, etc. are ignored
4. **Rotate keys**: Change SECRET_KEY if compromised (users will get new daily words)

---

## What You Get

After deployment:
- ✅ Public URL (e.g., `https://your-game.onrender.com`)
- ✅ HTTPS (SSL certificate included)
- ✅ Auto-updates when you push to GitHub
- ✅ Environment variable management
- ✅ Logs and monitoring

## Cost Summary

| Platform | Free Tier | Paid | Cold Starts | Ease |
|----------|-----------|------|-------------|------|
| **Render.com** | ✅ 750h/mo | $7/mo | Yes (15 min) | ⭐⭐⭐⭐⭐ |
| **Railway.app** | $5 trial | $5/mo | No | ⭐⭐⭐⭐⭐ |
| **Fly.io** | ✅ Small apps | ~$3/mo | No | ⭐⭐⭐⭐ |
| **Cloud Run** | ✅ 2M requests | ~$5/mo | Yes | ⭐⭐⭐ |

## My Recommendation

Start with **Render.com FREE tier**:
- Zero cost
- Easy deployment
- Good enough for a game with light traffic
- Upgrade later if you get lots of users
