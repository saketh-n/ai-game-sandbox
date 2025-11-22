# Quick Start Guide

Get up and running in 5 minutes! 🚀

## Prerequisites

- **Node.js** 18+ ([download](https://nodejs.org/))
- **Python** 3.8+ ([download](https://www.python.org/))
- **Anthropic API Key** ([get one](https://console.anthropic.com/))

## Step 1: Backend Setup (2 minutes)

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # Mac/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env
# OR manually create .env and add your key

# Start the server
uvicorn main:app --reload
```

✅ Backend running at `http://localhost:8000`

## Step 2: Frontend Setup (2 minutes)

**Open a NEW terminal** (keep backend running):

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

✅ Frontend running at `http://localhost:5173`

## Step 3: Try It Out! (1 minute)

1. Open browser to `http://localhost:5173`
2. Type a game theme: **"cyberpunk noir detective game"**
3. Press **Enter**
4. Watch the magic happen! ✨

## What You'll See

After a few seconds, you'll get:
- 🎮 Main character prompts (5 variations)
- 🌍 Environment assets (tiles, platforms, props)
- 👥 NPCs (allies, enemies, neutral)
- 🎨 Background scenes (multiple locations)

## Tips

- Click section headers to expand/collapse
- Edit any prompt directly in the text box
- Click "Copy" to grab a prompt for your image generator
- Try different themes:
  - "medieval fantasy RPG with dragons"
  - "pixel art space exploration game"
  - "Studio Ghibli inspired adventure"

## Troubleshooting

### Backend won't start?
- Check Python version: `python --version` (need 3.8+)
- Verify API key in `.env` file
- Make sure venv is activated (you should see `(venv)` in terminal)

### Frontend won't start?
- Check Node version: `node --version` (need 18+)
- Delete `node_modules` and run `npm install` again
- Try `npm run dev` from the `frontend/` directory

### API errors?
- Verify your Anthropic API key is valid
- Check backend logs in terminal
- Make sure backend is running on port 8000

### Nothing happens when I press Enter?
- Open browser console (F12) to check for errors
- Verify backend is running (visit `http://localhost:8000`)
- Check CORS settings if using different ports

## Next Steps

- Read `FEATURES.md` for detailed feature overview
- Check `README.md` for full documentation
- Explore the API docs at `http://localhost:8000/docs`

Happy generating! 🎮✨

