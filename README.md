# AI Video Game Asset Generator & Sandbox

A beautiful, modern web application for generating video game assets using AI, with real-time sandboxing capabilities.

## Features

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

1. Install dependencies using uv:
```bash
uv pip install -e .
```

Or with pip:
```bash
pip install -e .
```

2. Set up your FAL API key:
```bash
cp .env.example .env
# Edit .env and add your FAL_KEY from https://fal.ai/dashboard/keys
```

3. Run the example:
```bash
uv run src/example.py
```

Or with python:
```bash
python src/example.py
```

## CLI Usage

After installation, you can use the `generate-image` command:

### Basic Usage

```bash
# Simple generation with just a prompt
generate-image "A heroic knight character, white background"

# With inspiration images from URLs
generate-image "Similar character" --images https://example.com/ref1.jpg

# With local image files
generate-image "Similar character" --images ./reference.png

# Mix of URLs and local files
generate-image "Fantasy sword" --images https://example.com/sword.jpg ./ref.png
```

### Advanced Options

```bash
# Custom model and parameters
generate-image "Dragon character" \
  --model fal-ai/flux/schnell \
  --steps 30 \
  --cfg 8.0 \
  --size 512x512

# Generate multiple images
generate-image "Fantasy landscape" --num-images 4

# Save to specific directory
generate-image "Castle background" --output ./my_outputs

# Use specific seed for reproducibility
generate-image "Character design" --seed 42

# Quiet mode (less output)
generate-image "Quick test" --quiet
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
generate-image --list-models

# Character with reference
generate-image "Warrior character in armor" \
  --images ./character_ref.jpg \
  --cfg 7.5 \
  --steps 50

# High-res background
generate-image "Medieval castle courtyard, detailed" \
  --size 1920x1080 \
  --steps 40

# Multiple variations
generate-image "Fantasy sword concept" \
  --num-images 8 \
  --output ./sword_concepts
```

## Available Scripts

### Frontend
- `npm run dev` - Start the development server
- `npm run build` - Build for production
- `npm run preview` - Preview the production build
- `npm run lint` - Run ESLint

### Python
- `uv run src/example.py` - Run image generation examples
- `uv pip install -e .` - Install the package in editable mode
- `generate-image "your prompt"` - CLI tool for image generation (after installation)

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

## License

MIT



