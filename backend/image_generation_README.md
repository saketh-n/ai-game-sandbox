# Python Image Generation Module

This module provides a Python interface for generating images using the FAL AI API, specifically designed for video game asset generation.

## Features

- Generate images using various FAL AI models
- Support for all key parameters:
  - Model name selection
  - Custom prompts
  - Inspiration/reference images
  - CFG scale (guidance)
  - Number of inference steps
  - Image dimensions
  - Seed for reproducibility
- Progress tracking during generation
- Automatic image downloading

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your FAL API key:
```bash
cp .env.example .env
# Edit .env and add your FAL_KEY
```

Get your API key from: https://fal.ai/dashboard/keys

## Quick Start

```python
from image_generation import ImageGenerator, ImageGenerationConfig

# Initialize generator
generator = ImageGenerator()

# Create configuration
config = ImageGenerationConfig(
    model_name='fal-ai/flux/dev',
    prompt='A heroic knight character, centered, white background',
    cfg_scale=7.5,
    num_inference_steps=50,
    width=512,
    height=512,
    num_images=1
)

# Generate images
result = generator.generate_with_progress(config)

# Download results
saved_files = generator.download_images(result, output_dir='./output')
```

## Configuration Parameters

### ImageGenerationConfig

- **model_name** (str, required): The FAL AI model to use
  - Example: `'fal-ai/flux/dev'`, `'fal-ai/flux/schnell'`

- **prompt** (str, required): Text description of the image to generate

- **inspiration_images** (List[Union[str, Path, Image.Image, bytes]], optional): Reference images
  - Can be URLs (str), local file paths (str/Path), PIL Image objects, or raw bytes
  - URLs starting with http://, https://, or data: are used directly
  - Local files and PIL Images are automatically converted to base64 data URIs
  - Default: `[]` (no inspiration images)

- **cfg_scale** (float, optional): Guidance scale (how closely to follow the prompt)
  - Range: 0-20
  - Default: `7.5`

- **num_inference_steps** (int, optional): Number of denoising steps
  - Range: 1-150
  - Default: `50`

- **width** (int, optional): Image width in pixels
  - Minimum: 64
  - Default: `512`

- **height** (int, optional): Image height in pixels
  - Minimum: 64
  - Default: `512`

- **num_images** (int, optional): Number of images to generate
  - Minimum: 1
  - Default: `1`

- **seed** (int, optional): Random seed for reproducibility
  - Default: `None` (random)

## Available Models

Get list of common models:
```python
models = ImageGenerator.get_available_models()
```

Common models include:
- `fal-ai/flux/dev` - High quality, slower
- `fal-ai/flux/schnell` - Fast generation
- `fal-ai/flux-pro` - Professional quality
- `fal-ai/stable-diffusion-v3-medium`
- `fal-ai/fast-sdxl`
- `fal-ai/aura-flow`

## Examples

Run the example script:
```bash
python example.py
```

### Character Generation
```python
config = ImageGenerationConfig(
    model_name='fal-ai/flux/dev',
    prompt='A heroic knight character centered in the image, white background, high detail',
    cfg_scale=7.5,
    num_inference_steps=50,
    width=512,
    height=512
)
```

### Background Generation
```python
config = ImageGenerationConfig(
    model_name='fal-ai/flux/schnell',
    prompt='Medieval castle landscape, scenic view, detailed background',
    cfg_scale=8.0,
    num_inference_steps=30,
    width=1024,
    height=768,
    num_images=2
)
```

### Item with Reference Images

Using a URL:
```python
config = ImageGenerationConfig(
    model_name='fal-ai/flux/dev',
    prompt='Magical sword item, centered, white background, game asset style',
    inspiration_images=['https://example.com/reference.jpg'],  # URL
    cfg_scale=7.0,
    num_inference_steps=50,
    seed=42
)
```

Using a local file:
```python
from pathlib import Path

config = ImageGenerationConfig(
    model_name='fal-ai/flux/dev',
    prompt='Magical sword item, similar style',
    inspiration_images=[Path('./reference_images/sword.png')],  # Local file
    cfg_scale=7.0,
    num_inference_steps=50,
)
```

Using a PIL Image:
```python
from PIL import Image

reference_image = Image.open('./my_reference.jpg')
config = ImageGenerationConfig(
    model_name='fal-ai/flux/dev',
    prompt='Fantasy shield, similar style',
    inspiration_images=[reference_image],  # PIL Image object
    cfg_scale=7.5,
    num_inference_steps=50,
)
```

## API Methods

### ImageGenerator

#### `__init__(api_key: Optional[str] = None)`
Initialize the generator with your FAL API key.

#### `generate(config: ImageGenerationConfig) -> Dict[str, Any]`
Generate images without progress updates.

#### `generate_with_progress(config: ImageGenerationConfig, on_queue_update: Optional[callable] = None) -> Dict[str, Any]`
Generate images with progress callbacks.

#### `download_images(result: Dict[str, Any], output_dir: str = './output') -> List[str]`
Download generated images to local directory.

#### `get_available_models() -> List[str]`
Static method to get list of available models.

## Output Format

The generation methods return a dictionary with:
```python
{
    'images': [
        {
            'url': 'https://...',
            'width': 512,
            'height': 512,
            'content_type': 'image/jpeg'
        }
    ],
    'timings': {'inference': 2.5},
    'seed': 12345,
    'has_nsfw_concepts': [False],
    'prompt': 'your prompt',
    'model': 'fal-ai/flux/dev'
}
```

## Error Handling

The module includes validation and error handling:
- Configuration validation on creation
- API error wrapping with descriptive messages
- Automatic parameter range checking

## License

MIT
