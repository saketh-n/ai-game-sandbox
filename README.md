# AI Video Game Asset Generator & Sandbox

A beautiful, modern web application for generating video game assets using AI, with real-time sandboxing capabilities.

## Features

```
ai-asset-gen-sandbox/
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Route pages (Home, GenerateAssets)
│   │   ├── context/        # React Context for state management
│   │   ├── App.tsx         # Router setup
│   │   └── main.tsx        # Entry point
│   └── package.json
├── backend/
│   ├── main.py                      # FastAPI server
│   ├── cache_manager.py             # Prompt caching system
│   ├── component_cache_manager.py   # Component-level game caching
│   ├── game_cache_manager.py        # Monolithic game caching
│   └── requirements.txt
└── README.md
```
- 🎮 Video game theme input with intuitive UI
- 🎨 Beautiful gradient background with glassmorphism design
- ⚡ Built with React, TypeScript, and Tailwind CSS
- 🚀 Fast development with Vite
- 🖼️ Python-based image generation with FAL AI integration

## Getting Started

### Prerequisites

- Node.js (v18 or higher recommended)
- npm or yarn
- Python 3.9+ (for image generation)
- [uv](https://github.com/astral-sh/uv) (recommended for Python dependency management)

### Frontend Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser and navigate to `http://localhost:5173`

### Python Image Generation Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Set up your FAL API key:
```bash
cp .env.example .env
# Edit .env and add your FAL_KEY from https://fal.ai/dashboard/keys
```
4. Run the example or use the CLI:
```bash
# Run example script
uv run example.py

# Or use the CLI tool
uv run generate-image "Your prompt here"
```

## CLI Usage

From the `backend` directory, use `uv run generate-image` to run the CLI tool:

### Basic Usage

```bash
cd backend

# Simple generation with just a prompt
uv run generate-image "A heroic knight character, white background"

# With inspiration images from URLs
uv run generate-image "Similar character" --images https://example.com/ref1.jpg

# With local image files
uv run generate-image "Similar character" --images ./reference.png

# Mix of URLs and local files
uv run generate-image "Fantasy sword" --images https://example.com/sword.jpg ./ref.png
```

### Advanced Options

```bash
# Custom model and parameters
uv run generate-image "Dragon character" \
  --model fal-ai/flux/schnell \
  --steps 30 \
  --cfg 8.0 \
  --size 512x512

# Generate multiple images
uv run generate-image "Fantasy landscape" --num-images 4

# Save to specific directory
uv run generate-image "Castle background" --output ./my_outputs

# Use specific seed for reproducibility
uv run generate-image "Character design" --seed 42

# Quiet mode (less output)
uv run generate-image "Quick test" --quiet
```

### CLI Options

- `--images`, `-i`: Inspiration images (URLs or file paths)
- `--model`, `-m`: Model name (default: fal-ai/flux/dev)
- `--cfg`, `-c`: CFG scale/guidance (default: 7.5)
- `--steps`, `-s`: Inference steps (default: 25)
- `--size`: Image size as WIDTHxHEIGHT (default: 1024x1024)
- `--num-images`, `-n`: Number of images (default: 1)
- `--seed`: Random seed for reproducibility
- `--output`, `-o`: Output directory (default: ./output)
- `--quiet`, `-q`: Suppress progress messages
- `--list-models`: List available models

### Examples

```bash
# List available models
uv run generate-image --list-models

# Character with reference
uv run generate-image "Warrior character in armor" \
  --images ./character_ref.jpg \
  --cfg 7.5 \
  --steps 50

# High-res background
uv run generate-image "Medieval castle courtyard, detailed" \
  --size 1920x1080 \
  --steps 40

# Multiple variations
uv run generate-image "Fantasy sword concept" \
  --num-images 8 \
  --output ./sword_concepts
```

## Available Scripts

### Frontend
- `npm run dev` - Start the development server
- `npm run build` - Build for production
- `npm run preview` - Preview the production build
- `npm run lint` - Run ESLint

### Python Backend
(Run from `backend/` directory)
- `uv sync` - Install dependencies and set up virtual environment
- `uv run example.py` - Run image generation examples
- `uv run generate-image "your prompt"` - CLI tool for image generation
## Usage

1. **Enter a theme**: Type a video game theme in the input box (e.g., "cyberpunk noir detective game")
2. **Press Enter**: The frontend sends your theme to the backend
3. **AI Processing**: Backend calls Claude API to generate detailed asset prompts
4. **View Results**: See AI-generated prompts organized by:
   - 🎮 **Main Character** - Multiple variations with detailed descriptions
   - 🌍 **Environment Assets** - Ground tiles, platforms, props, trees, rocks, etc.
   - 👥 **NPCs** - Allies, enemies, and neutral characters
   - 🎨 **Background Scenes** - Full scene compositions for different levels/areas
5. **Edit & Copy**: Each prompt is editable and has a copy button for easy use

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Main Endpoints

**POST** `/generate-asset-prompts`
- Generates asset prompts (uses cache if available)
- Request: `{ "prompt": "game theme" }`
- Response: `{ "result": "...", "cached": false }`

**GET** `/cached-prompts`
- Returns list of all cached prompts
- Response: `{ "prompts": [...], "count": 5 }`

**POST** `/fetch-cached-prompt`
- Fetches full result for a cached prompt
- Request: `{ "prompt": "exact prompt text" }`
- Response: `{ "prompt": "...", "result": "...", "timestamp": "..." }`

See `CACHING_FEATURE.md` for detailed caching documentation.
This will create a virtual environment (`backend/.venv`) and install all dependencies.

- ✨ **Beautiful UI**: Modern gradient design with glassmorphism effects
- 🤖 **AI-Powered**: Uses Claude Sonnet 4.5 for intelligent prompt generation
- ⚡ **Fast & Responsive**: Built with Vite and FastAPI
- 🔄 **Loading States**: Smooth animations while waiting for AI responses
- ❌ **Error Handling**: Clear error messages if something goes wrong
- 📝 **Type-Safe**: Full TypeScript support on frontend
- 📋 **Structured Output**: Organized, collapsible sections for each asset category
- ✏️ **Editable Prompts**: Modify any generated prompt in real-time
- 📄 **One-Click Copy**: Copy button for each prompt variation
- 🎯 **Comprehensive Assets**: Characters, environments, NPCs, and backgrounds all generated at once
- 💾 **Smart Caching**: Instant results for previously generated prompts (saves time & API costs)
- 🕒 **Prompt History**: View and reload recent prompts with one click
- ⚡ **Instant Loading**: Cached prompts load in <1 second vs 5-15 seconds for new generation

## Tech Stack

### Frontend
- **React** - UI library
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Vite** - Next-generation frontend tooling

### Backend
- **Python 3.9+** - Image generation module
- **FAL AI** - AI image generation API
- **uv** - Fast Python package manager

## Prompts
The following are prompt templates for generating various assets

### Character
```
{user_instruction}
Generate a character this centered within the image. Make the background white.
The character is well visible within the scene and is well rendered
```

### Background
```
{user_instruction}
Make this background fit the scene and well visible. Focus on making the background be well shown
```

### Item
```
{user_instruction}
Make this item be visible within the center of the image. Make the background white around the item
```

## Performance & Caching

The system implements **intelligent component-level caching** for dramatic performance improvements:

- **80-90% faster** game regeneration after modifications
- **Granular caching** of backgrounds, characters, mobs, and collectibles
- **Automatic invalidation** when assets change
- **Mix and match** cached components across generations

For detailed information, see [COMPONENT_CACHING_SYSTEM.md](./COMPONENT_CACHING_SYSTEM.md)

### API Endpoints for Cache Management

```bash
# Get component cache statistics
GET /component-cache/stats

# Clear component cache
DELETE /component-cache

# Get game cache list (legacy monolithic cache)
GET /game-cache/list

# Clear game cache
DELETE /game-cache
```

## License

MIT
