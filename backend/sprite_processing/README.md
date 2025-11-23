# Sprite Processing Module

A Python module for processing game sprites: background removal, sprite sheet assembly, and Phaser.js configuration generation.

## Features

- **Background Removal**: Automatically remove white/colored backgrounds from character sprites
- **Auto-Cropping**: Trim transparent borders with configurable padding
- **Sprite Sheet Assembly**: Create horizontal or grid-based sprite sheets
- **Multi-Animation Support**: Combine multiple animations (walk, idle, jump) into one sheet
- **Phaser.js Integration**: Generate complete Phaser.js code and configurations
- **CLI Tool**: Easy-to-use command-line interface
- **Batch Processing**: Process multiple sprites at once

## Installation

The module is already included in the project. Install dependencies:

```bash
uv sync
```

## Quick Start

### CLI Usage

```bash
# Process a single character sprite
uv run process-sprites character.png -o output/character.png

# Process walk cycle frames
uv run process-sprites walk_*.png -o walk_cycle.png --generate-phaser

# Create grid sprite sheet with custom settings
uv run process-sprites frame*.png \
  -o sprites/hero.png \
  --layout grid \
  --columns 4 \
  --frame-width 64 \
  --frame-height 64 \
  --generate-phaser \
  --phaser-key hero
```

### Python API

```python
from sprite_processing import BackgroundRemover, SpriteSheetBuilder, PhaserConfigGenerator

# Remove background from a sprite
bg_remover = BackgroundRemover()
processed = bg_remover.process_sprite("character.png")
processed.save("character_no_bg.png")

# Create sprite sheet
builder = SpriteSheetBuilder()
frames = [Image.open(f"walk_{i}.png") for i in range(8)]
sprite_sheet, metadata = builder.create_horizontal_sheet(frames)

# Generate Phaser.js configuration
phaser_gen = PhaserConfigGenerator()
phaser_gen.save_phaser_config(
    metadata,
    output_path="output/character",
    texture_key="player",
    generate_code=True
)
```

## Module Components

### 1. BackgroundRemover

Removes solid color backgrounds from sprites.

**Features:**
- Auto-detect white backgrounds
- Remove specific colors with tolerance
- Auto-crop transparent borders
- Batch processing

**Example:**
```python
from sprite_processing import BackgroundRemover
from PIL import Image

remover = BackgroundRemover(threshold=240)

# Remove white background
sprite = remover.remove_background("sprite.png")

# Remove specific color (e.g., green screen)
sprite = remover.remove_background(
    "sprite.png",
    background_color=(0, 255, 0),  # Green
    tolerance=30
)

# Full processing pipeline
processed = remover.process_sprite(
    "sprite.png",
    output_size=(128, 128),  # Resize
    auto_crop_enabled=True,   # Crop transparent borders
    crop_padding=5            # Leave 5px padding
)
```

### 2. SpriteSheetBuilder

Assembles individual frames into sprite sheets.

**Layouts:**
- **Horizontal**: Single row of frames
- **Grid**: Multi-row grid layout
- **Multi-Animation**: Combine different animations

**Example:**
```python
from sprite_processing import SpriteSheetBuilder
from PIL import Image

builder = SpriteSheetBuilder()

# Load frames
walk_frames = [Image.open(f"walk_{i}.png") for i in range(8)]

# Create horizontal sprite sheet
sprite_sheet, metadata = builder.create_horizontal_sheet(
    walk_frames,
    frame_width=64,
    frame_height=64,
    spacing=2
)

# Create grid sprite sheet
sprite_sheet, metadata = builder.create_grid_sheet(
    walk_frames,
    columns=4,
    spacing=1
)

# Create multi-animation sprite sheet
animations = {
    'idle': [Image.open(f"idle_{i}.png") for i in range(2)],
    'walk': [Image.open(f"walk_{i}.png") for i in range(8)],
    'jump': [Image.open(f"jump_{i}.png") for i in range(4)]
}

sprite_sheet, metadata = builder.create_animation_sheet(
    animations,
    layout='horizontal'
)

# Save sprite sheet
builder.save_sprite_sheet(
    sprite_sheet,
    metadata,
    "character.png",
    save_metadata=True  # Also saves character.json
)
```

### 3. PhaserConfigGenerator

Generates Phaser.js-compatible configurations and code.

**Generates:**
- Sprite sheet load configuration
- Animation definitions
- Complete Phaser.js game code
- JSON configuration files

**Example:**
```python
from sprite_processing import PhaserConfigGenerator

generator = PhaserConfigGenerator()

# Generate spritesheet config
config = generator.generate_spritesheet_config(
    metadata,
    texture_key='player',
    sprite_sheet_path='assets/sprites/player.png'
)

# Generate animation configurations
animations = generator.generate_character_animations(
    metadata,
    texture_key='player',
    walk_frame_rate=10,
    idle_frame_rate=5
)

# Generate complete Phaser.js code
code = generator.generate_phaser_code(
    metadata,
    texture_key='player',
    sprite_sheet_path='assets/sprites/player.png',
    class_name='GameScene'
)

# Save everything
files = generator.save_phaser_config(
    metadata,
    output_path='output/player',
    texture_key='player',
    sprite_sheet_path='assets/sprites/player.png',
    generate_code=True
)
# Creates: player_config.json and player_scene.js
```

## CLI Reference

### Basic Usage

```bash
uv run process-sprites [images...] -o OUTPUT [options]
```

### Options

**Input/Output:**
- `images` - Input image files (required)
- `-o, --output OUTPUT` - Output sprite sheet path (required)

**Background Removal:**
- `--threshold N` - White background threshold (0-255, default: 240)
- `--no-crop` - Disable auto-cropping
- `--crop-padding N` - Padding around cropped content (default: 5)

**Frame Sizing:**
- `--frame-width N` - Fixed frame width
- `--frame-height N` - Fixed frame height

**Layout:**
- `--layout {horizontal,grid}` - Sprite sheet layout (default: horizontal)
- `--columns N` - Columns for grid layout (default: 8)
- `--spacing N` - Spacing between frames (default: 0)

**Phaser.js:**
- `--generate-phaser` - Generate Phaser.js configuration
- `--phaser-key KEY` - Phaser texture key (default: character)
- `--phaser-path PATH` - Path for Phaser to load sprite sheet

### Examples

#### Example 1: Basic Sprite Processing
```bash
# Remove background and create sprite sheet
uv run process-sprites character.png -o output/character.png
```

#### Example 2: Walk Cycle Animation
```bash
# Process 8 walk frames into horizontal sprite sheet
uv run process-sprites walk_0.png walk_1.png walk_2.png walk_3.png \
                       walk_4.png walk_5.png walk_6.png walk_7.png \
  -o walk_cycle.png \
  --generate-phaser \
  --phaser-key hero_walk
```

#### Example 3: Grid Layout
```bash
# Create 4x2 grid sprite sheet
uv run process-sprites frame*.png \
  -o sprites/character.png \
  --layout grid \
  --columns 4 \
  --spacing 2
```

#### Example 4: Fixed Frame Size
```bash
# Resize all frames to 64x64
uv run process-sprites *.png \
  -o character.png \
  --frame-width 64 \
  --frame-height 64 \
  --generate-phaser
```

#### Example 5: Custom Background Color
```bash
# For backgrounds other than white, use Python API
python -c "
from sprite_processing import BackgroundRemover
remover = BackgroundRemover()
sprite = remover.remove_background('sprite.png', background_color=(0, 255, 0))
sprite.save('output.png')
"
```

## Generated Phaser.js Code

When using `--generate-phaser`, the module generates:

### 1. Configuration JSON (`*_config.json`)
```json
{
  "spritesheet": {
    "key": "character",
    "url": "assets/sprites/character.png",
    "frameConfig": {
      "frameWidth": 64,
      "frameHeight": 64,
      "startFrame": 0,
      "endFrame": 7
    }
  },
  "animations": {
    "walk-right": {
      "key": "walk-right",
      "frames": [...],
      "frameRate": 10,
      "repeat": -1
    }
  }
}
```

### 2. Phaser.js Scene Code (`*_scene.js`)
```javascript
class GameScene extends Phaser.Scene {
    preload() {
        this.load.spritesheet('character', 'assets/sprites/character.png', {
            frameWidth: 64,
            frameHeight: 64
        });
    }

    create() {
        this.player = this.add.sprite(400, 300, 'character');

        this.anims.create({
            key: 'walk-right',
            frames: this.anims.generateFrameNumbers('character', {
                start: 0, end: 7
            }),
            frameRate: 10,
            repeat: -1
        });

        this.player.play('walk-right');
    }

    update() {
        // Movement controls with left/right flip
        if (this.cursors.left.isDown) {
            this.player.setFlipX(true);
            this.player.play('walk-left', true);
        }
        else if (this.cursors.right.isDown) {
            this.player.setFlipX(false);
            this.player.play('walk-right', true);
        }
    }
}
```

## Running Examples

```bash
# Run the comprehensive example script
uv run python sprite_example.py
```

This demonstrates:
1. Processing experiment characters
2. Creating walk cycle sprite sheets
3. Multi-animation sprite sheets
4. Phaser.js code generation

Output files are saved to `sprite_processing/examples/`

## Workflow

### Typical Game Asset Pipeline

1. **Generate Characters** (using image_generation module)
```bash
uv run generate-image "pixel art warrior character, white background" \
  --model fal-ai/alpha-image-232/text-to-image
```

2. **Remove Background & Process**
```bash
uv run process-sprites generated_character.png \
  -o sprites/warrior.png \
  --generate-phaser \
  --phaser-key warrior
```

3. **Use in Phaser.js Game**
```javascript
// Load the generated scene code
import { GameScene } from './warrior_scene.js';

const config = {
    type: Phaser.AUTO,
    width: 800,
    height: 600,
    scene: GameScene
};

const game = new Phaser.Game(config);
```

## Integration with Image Generation

The sprite processing module works seamlessly with the image generation module:

```python
from image_generation import ImageGenerator, ImageGenerationConfig
from sprite_processing import BackgroundRemover, SpriteSheetBuilder

# Generate character frames
generator = ImageGenerator()

frames = []
for i in range(8):
    config = ImageGenerationConfig(
        model_name="fal-ai/alpha-image-232/text-to-image",
        prompt=f"pixel art character walking, frame {i}, white background",
        width=512,
        height=512
    )
    result = generator.generate(config)
    # Download and process frame
    # ...

# Process into sprite sheet
remover = BackgroundRemover()
processed_frames = remover.batch_process(frames)

builder = SpriteSheetBuilder()
sprite_sheet, metadata = builder.create_horizontal_sheet(processed_frames)
```

## Tips & Best Practices

### Background Removal
- **White backgrounds**: Use default threshold (240)
- **Colored backgrounds**: Specify `background_color` and adjust `tolerance`
- **Shadows**: Increase threshold to preserve subtle shadows
- **Pixel art**: Use higher threshold (250+) for crisp edges

### Sprite Sheet Layout
- **Walk cycles**: Use horizontal layout (easier to visualize)
- **Multiple animations**: Use grid layout or multi-animation sheets
- **Large sprite sets**: Use grid with 8-12 columns for manageability

### Frame Sizing
- **Uniform sizes**: Better for game engines, use `--frame-width` and `--frame-height`
- **Pixel art**: Preserve original size or use multiples (32, 64, 128)
- **HD sprites**: Consider power-of-2 sizes (256, 512, 1024)

### Phaser.js Integration
- Use descriptive texture keys (`hero`, `enemy_goblin`, `item_sword`)
- Set appropriate frame rates (8-12 for walk, 4-6 for idle, 15-20 for attacks)
- Keep sprite sheet file sizes reasonable (<2MB for mobile)

## File Structure

```
sprite_processing/
├── __init__.py              # Module exports
├── background_remover.py    # Background removal logic
├── sprite_sheet_builder.py  # Sprite sheet assembly
├── phaser_config.py         # Phaser.js code generation
├── cli.py                   # Command-line interface
├── README.md                # This file
└── examples/                # Generated examples
    ├── character_no_bg.png
    ├── character_sheet.png
    ├── character_sheet.json
    └── character/
        ├── pixel_character_config.json
        └── pixel_character_scene.js
```

## Metadata Format

Sprite sheet metadata (JSON):

```json
{
  "frame_count": 8,
  "frame_width": 64,
  "frame_height": 64,
  "spacing": 0,
  "sheet_width": 512,
  "sheet_height": 64,
  "frames": [
    {
      "frame": 0,
      "x": 0,
      "y": 0,
      "width": 64,
      "height": 64
    }
  ],
  "animations": {
    "walk": {
      "start_frame": 0,
      "end_frame": 7,
      "frame_count": 8
    }
  }
}
```

## Requirements

- Python 3.12+
- Pillow (PIL) - Image processing
- NumPy - Array operations

All dependencies are managed via `pyproject.toml`.

## License

MIT
