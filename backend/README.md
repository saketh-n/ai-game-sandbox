# AI Game Asset Generator

Generate playable HTML5 platformer games from character sprites and background images.

## Quick Start

### Prerequisites

- Python 3.12+
- uv package manager

### Installation

```bash
# Install dependencies
uv sync
```

### Generate a Game

```bash
# Basic usage
uv run python game_generator.py \
  --character path/to/character_sprite.png \
  --background path/to/background.png

# With custom options
uv run python game_generator.py \
  --character animated_sprites/pineapple_warrior_spritesheet.png \
  --background test_background.png \
  --frames 8 \
  --output my_game \
  --name "MyAwesomeGame"
```

### Play the Game

```bash
cd my_game
python3 run_game.py
```

Or open http://localhost:8080/game.html in your browser.

## Project Structure

```
backend/
├── game_generator.py           # Main unified game generator CLI
├── image_generation/          # Image generation using FAL API
│   ├── generator.py
│   └── config.py
├── sprite_processing/         # Sprite sheet processing
│   ├── background_remover.py
│   ├── sprite_sheet_builder.py
│   └── phaser_config.py
├── scene_builder/             # Game scene building
│   ├── background_analyzer.py
│   ├── scene_generator.py
│   └── web_exporter.py
└── main.py                    # FastAPI server (separate from game generation)
```

## Features

### Game Generator (`game_generator.py`)

The unified game generator takes character sprites and background images and produces a complete playable HTML5 platformer game.

**Features:**
- Automatic platform detection using proportional scaling
- Character sprite processing (8-frame walking animation)
- Double jump mechanics
- Responsive canvas sizing
- Real-time stats display
- Keyboard controls (arrows, space, R for reset)

**Command-line Options:**
```
--character, -c    Path to character sprite sheet (required)
--background, -b   Path to background image (required)
--frames, -f       Number of animation frames (default: 8)
--output, -o       Output directory (default: generated_game)
--name, -n         Game name (default: PlatformerGame)
```

### Sprite Requirements

**Character Sprite Sheet:**
- Format: PNG with transparent background
- Layout: Horizontal sprite sheet (frames side-by-side)
- Frames: Typically 8 frames for walking animation
- Example: 920x187px (8 frames of 115x187px each)

**Background Image:**
- Format: PNG or JPG
- Recommended size: 1024x768px (4:3 aspect ratio)
- Style: Should have clear walkable platforms

### Generated Game Structure

```
generated_game/
├── game.html              # Main game file
├── run_game.py            # HTTP server script
├── scene_config.json      # Game configuration
└── assets/
    ├── character_sprite.png
    └── background.png
```

## Game Controls

- **← →** : Move left/right
- **SPACE** : Jump (double jump available!)
- **R** : Reset character position

## Modules

### Image Generation (`image_generation/`)

Generate game assets using FAL AI's image generation models.

```python
from image_generation.generator import ImageGenerator
from image_generation.config import ImageGenerationConfig

generator = ImageGenerator(api_key="your_fal_key")
result = generator.generate(
    config=ImageGenerationConfig(
        model_name="fal-ai/alpha-image-232/text-to-image",
        prompt="pixel art character sprite sheet"
    )
)
```

### Sprite Processing (`sprite_processing/`)

Process character sprite sheets, remove backgrounds, create animations.

```python
from sprite_processing.background_remover import BackgroundRemover

remover = BackgroundRemover()
processed = remover.remove_background(image_path)
```

### Scene Building (`scene_builder/`)

Analyze backgrounds, generate game scenes, export to HTML5.

```python
from scene_builder.web_exporter import WebGameExporter

exporter = WebGameExporter()
exporter.export_game(scene_config, output_path)
```

## API Server (Optional)

The project also includes a FastAPI server for web-based asset generation:

```bash
# Start the API server
uv run uvicorn main:app --reload

# Access at http://localhost:8000
# API docs at http://localhost:8000/docs
```

**API Endpoints:**
- `POST /generate-asset-prompts` - Generate game asset prompts using Claude
- `POST /generate-image-asset` - Generate images from prompts
- `GET /cached-prompts` - List cached prompts
- `POST /fetch-cached-prompt` - Fetch specific cached result

## Environment Variables

Create a `.env` file in the backend directory:

```env
# Required for game generator (platform detection with Claude Vision)
ANTHROPIC_API_KEY=your_anthropic_key

# Required for API server (image generation)
FAL_KEY=your_fal_key

# Optional
LOG_LEVEL=INFO
```

**Note**: The `ANTHROPIC_API_KEY` is required for the game generator to analyze background images and detect walkable platforms using Claude's vision API.

## Examples

### Example 1: Generate Pineapple Warrior Game

```bash
uv run python game_generator.py \
  --character animated_sprites/pineapple_warrior_spritesheet.png \
  --background test_background.png \
  --output pineapple_game \
  --name "PineappleWarrior"

cd pineapple_game
python3 run_game.py
```

### Example 2: Custom Character and Background

```bash
# First, generate assets using the API or your own images
# Then create the game
uv run python game_generator.py \
  --character my_character.png \
  --background my_background.png \
  --frames 8 \
  --output my_custom_game
```

## Platform Detection

The game generator uses **Claude Vision API (Sonnet 4.5)** to automatically analyze background images and identify walkable platforms.

**How it works:**
1. Background image is sent to Claude's vision API
2. Claude identifies only green grass platforms (walkable surfaces)
3. Decorative elements (trees, fences, water) are excluded
4. Platform positions, sizes, and gaps are precisely calculated
5. Optimal spawn point is determined

**Rules Claude follows:**
- Only green grass surfaces are walkable
- Trees are decorative (no collision)
- Fences are decorative (no collision)
- Water/sky areas are not walkable
- Gaps between platforms are identified for jump mechanics

This vision-based approach ensures accurate platform detection for any background image, without manual configuration.

## Troubleshooting

### CORS Issues
If the game doesn't load when opened directly, use the provided `run_game.py` script to start a local HTTP server.

### Assets Not Loading
Ensure asset paths are correct and files exist. The generator will copy assets to the output directory automatically.

### Platform Detection Issues
Platform positions are calculated proportionally based on image dimensions. For best results, use backgrounds with clear horizontal platforms.

## Development

### Running Tests

```bash
# Test game generation
uv run python game_generator.py --character test_characeter_sprites.png --background test_background.png

# Start API server for testing
uv run uvicorn main:app --reload
```

### Code Structure

The codebase is organized into three main modules:

1. **image_generation**: FAL AI integration for generating game assets
2. **sprite_processing**: Image processing utilities for sprites
3. **scene_builder**: Phaser.js game generation and export

Each module is independent and can be used separately or as part of the unified `game_generator.py` workflow.

## License

MIT

## Credits

- Built with [Phaser 3](https://phaser.io/) game framework
- Image generation powered by [FAL AI](https://fal.ai/)
- Prompt generation using [Anthropic Claude](https://www.anthropic.com/)
