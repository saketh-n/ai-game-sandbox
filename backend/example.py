"""
Example usage of the image generation module
"""

import os
from dotenv import load_dotenv
from image_generation import ImageGenerator, ImageGenerationConfig


def main():
    # Load environment variables from .env file
    load_dotenv()

    # Initialize the generator
    generator = ImageGenerator()

    # Example 1: Basic image generation
    print("Example 1: Basic character generation")
    config = ImageGenerationConfig(
        model_name='fal-ai/flux/dev',
        prompt='A heroic knight character centered in the image, white background, high detail',
        cfg_scale=7.5,
        num_inference_steps=50,
        width=512,
        height=512,
        num_images=1
    )

    result = generator.generate_with_progress(config)
    print(f"Generated {len(result['images'])} image(s)")
    print(f"Seed used: {result['seed']}")

    # Download the images
    saved_files = generator.download_images(result, output_dir='./output/characters')
    print(f"Saved to: {saved_files}")

    # Example 2: Background generation with custom steps
    print("\nExample 2: Background generation")
    config = ImageGenerationConfig(
        model_name='fal-ai/flux/schnell',
        prompt='Medieval castle landscape, scenic view, detailed background',
        cfg_scale=8.0,
        num_inference_steps=30,
        width=1024,
        height=768,
        num_images=2
    )

    result = generator.generate_with_progress(config)
    saved_files = generator.download_images(result, output_dir='./output/backgrounds')

    # Example 3: Item generation with inspiration image (URL)
    print("\nExample 3: Item with inspiration image from URL")
    config = ImageGenerationConfig(
        model_name='fal-ai/flux/dev',
        prompt='Magical sword item, centered, white background, game asset style',
        inspiration_images=[
            'https://example.com/reference-sword.jpg'  # Can use URL directly
        ],
        cfg_scale=7.0,
        num_inference_steps=50,
        width=512,
        height=512,
        num_images=1,
        seed=42  # For reproducible results
    )

    result = generator.generate_with_progress(config)
    saved_files = generator.download_images(result, output_dir='./output/items')

    # Example 3b: Item generation with local image file
    print("\nExample 3b: Item with inspiration from local file")
    from pathlib import Path

    # Assuming you have a local reference image
    local_image_path = Path('./reference_images/sword.png')
    if local_image_path.exists():
        config = ImageGenerationConfig(
            model_name='fal-ai/flux/dev',
            prompt='Magical sword item, similar style, centered, white background',
            inspiration_images=[
                local_image_path  # Can use local file path
            ],
            cfg_scale=7.0,
            num_inference_steps=50,
        )
        result = generator.generate_with_progress(config)
        saved_files = generator.download_images(result, output_dir='./output/items')
    else:
        print(f"Skipping - no local reference image found at {local_image_path}")

    # Example 3c: Using PIL Image object
    print("\nExample 3c: Using PIL Image object as inspiration")
    from PIL import Image

    # You can also use PIL Image objects directly
    try:
        pil_image = Image.new('RGB', (100, 100), color='red')  # Example image
        config = ImageGenerationConfig(
            model_name='fal-ai/flux/dev',
            prompt='Fantasy shield with red tones, game asset',
            inspiration_images=[
                pil_image  # Can use PIL Image directly
            ],
            cfg_scale=7.5,
            num_inference_steps=50,
        )
        result = generator.generate_with_progress(config)
        saved_files = generator.download_images(result, output_dir='./output/items')
    except Exception as e:
        print(f"PIL Image example skipped: {e}")

    # Example 4: Using custom progress callback
    print("\nExample 4: With custom progress tracking")

    def progress_callback(update):
        status = update.get('status')
        print(f"Status: {status}")
        if status == 'IN_PROGRESS':
            logs = update.get('logs', [])
            for log in logs:
                print(f"  {log.get('message', '')}")

    config = ImageGenerationConfig(
        model_name='fal-ai/flux/dev',
        prompt='Mystical forest NPC character, fantasy style',
        cfg_scale=7.5,
        num_inference_steps=40,
    )

    result = generator.generate_with_progress(config, on_queue_update=progress_callback)
    saved_files = generator.download_images(result, output_dir='./output/npcs')

    print("\nAll examples completed!")
    print(f"\nAvailable models: {ImageGenerator.get_available_models()}")


if __name__ == '__main__':
    main()
