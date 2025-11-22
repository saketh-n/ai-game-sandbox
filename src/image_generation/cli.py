#!/usr/bin/env python3
"""
Command-line interface for image generation using FAL AI
"""

import argparse
import sys
from pathlib import Path
from typing import List, Union
from dotenv import load_dotenv

from .generator import ImageGenerator
from .config import ImageGenerationConfig


def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate images using FAL AI API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic generation with just a prompt
  %(prog)s "A heroic knight character, white background"

  # With inspiration images from URLs
  %(prog)s "Similar character" --images https://example.com/ref1.jpg https://example.com/ref2.jpg

  # With local image files
  %(prog)s "Similar character" --images ./ref1.png ./ref2.png

  # Mix of URLs and local files
  %(prog)s "Fantasy sword" --images https://example.com/sword.jpg ./reference.png

  # Custom parameters
  %(prog)s "Dragon character" --model fal-ai/flux/schnell --steps 30 --cfg 8.0 --size 512x512

  # Save to specific directory
  %(prog)s "Castle background" --output ./my_outputs/backgrounds

  # Generate multiple images
  %(prog)s "Fantasy landscape" --num-images 4
        """
    )

    parser.add_argument(
        'prompt',
        type=str,
        nargs='?',
        help='Text prompt describing the image to generate'
    )

    parser.add_argument(
        '--images', '-i',
        nargs='*',
        default=[],
        help='Inspiration images (URLs or local file paths). Can provide multiple.'
    )

    parser.add_argument(
        '--model', '-m',
        type=str,
        default='fal-ai/alpha-image-232/text-to-image',
        help='Model name to use (default: fal-ai/flux/dev)'
    )

    parser.add_argument(
        '--cfg', '-c',
        type=float,
        default=3.5,
        help='CFG scale / guidance scale (default: 7.5, range: 0-20)'
    )

    parser.add_argument(
        '--steps', '-s',
        type=int,
        default=25,
        help='Number of inference steps (default: 25)'
    )

    parser.add_argument(
        '--size',
        type=str,
        default='1024x1024',
        help='Image size in WIDTHxHEIGHT format (default: 1024x1024)'
    )

    parser.add_argument(
        '--num-images', '-n',
        type=int,
        default=1,
        help='Number of images to generate (default: 1)'
    )

    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        help='Random seed for reproducibility (optional)'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default='./output',
        help='Output directory for generated images (default: ./output)'
    )

    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='FAL API key (default: from FAL_KEY environment variable)'
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress progress messages'
    )

    parser.add_argument(
        '--list-models',
        action='store_true',
        help='List available models and exit'
    )

    return parser.parse_args()


def parse_size(size_str: str) -> tuple:
    """Parse size string like '1024x768' into (width, height)"""
    try:
        width, height = size_str.lower().split('x')
        return int(width), int(height)
    except (ValueError, AttributeError):
        raise ValueError(
            f"Invalid size format: {size_str}. Use WIDTHxHEIGHT (e.g., 1024x768)"
        )


def process_images(image_paths: List[str]) -> List[Union[str, Path]]:
    """
    Process image paths/URLs into appropriate format

    Args:
        image_paths: List of URLs or file paths

    Returns:
        List of URLs (as str) or Path objects for local files
    """
    processed = []

    for img_path in image_paths:
        # Check if it's a URL
        if img_path.startswith('http://') or img_path.startswith('https://'):
            processed.append(img_path)
        else:
            # Treat as local file path
            path = Path(img_path)
            if not path.exists():
                print(f"Warning: Image file not found: {path}", file=sys.stderr)
                print(f"Skipping this image...", file=sys.stderr)
                continue
            processed.append(path)

    return processed


def main():
    """Main CLI entry point"""
    # Load environment variables
    load_dotenv()

    args = parse_args()

    # List models if requested
    if args.list_models:
        print("Available models:")
        for model in ImageGenerator.get_available_models():
            print(f"  - {model}")
        return 0

    # Validate prompt is provided if not just listing models
    if not args.prompt:
        print("Error: prompt is required", file=sys.stderr)
        print("Run 'generate-image --help' for usage information", file=sys.stderr)
        return 1

    try:
        # Initialize generator
        if not args.quiet:
            print("Initializing image generator...")

        generator = ImageGenerator(api_key=args.api_key)

        # Parse size
        width, height = parse_size(args.size)

        # Process inspiration images
        inspiration_images = process_images(args.images)

        if args.images and not inspiration_images:
            print("Error: No valid inspiration images provided", file=sys.stderr)
            return 1

        # Create configuration
        config = ImageGenerationConfig(
            model_name=args.model,
            prompt=args.prompt,
            inspiration_images=inspiration_images,
            cfg_scale=args.cfg,
            num_inference_steps=args.steps,
            width=width,
            height=height,
            num_images=args.num_images,
            seed=args.seed,
        )

        # Display configuration
        if not args.quiet:
            print(f"\nConfiguration:")
            print(f"  Model: {config.model_name}")
            print(f"  Prompt: {config.prompt}")
            print(f"  Size: {config.width}x{config.height}")
            print(f"  CFG Scale: {config.cfg_scale}")
            print(f"  Steps: {config.num_inference_steps}")
            print(f"  Number of images: {config.num_images}")
            if config.seed:
                print(f"  Seed: {config.seed}")
            if inspiration_images:
                print(f"  Inspiration images: {len(inspiration_images)}")
                for img in inspiration_images:
                    print(f"    - {img}")
            print()

        # Generate images
        def progress_callback(update):
            if not args.quiet:
                status = update.get('status')
                if status == 'IN_PROGRESS':
                    logs = update.get('logs', [])
                    for log in logs:
                        message = log.get('message', '')
                        if message:
                            print(f"  {message}")
                elif status == 'IN_QUEUE':
                    print("  Queued for generation...")

        if not args.quiet:
            print("Generating images...")

        result = generator.generate_with_progress(
            config,
            on_queue_update=progress_callback
        )

        # Download images
        if not args.quiet:
            print(f"\nDownloading {len(result['images'])} image(s)...")

        saved_files = generator.download_images(result, output_dir=args.output)

        # Display results
        print(f"\n✓ Successfully generated {len(saved_files)} image(s)")
        print(f"  Seed used: {result['seed']}")
        print(f"  Inference time: {result['timings'].get('inference', 'N/A')}s")
        print(f"\nSaved to:")
        for file_path in saved_files:
            print(f"  - {file_path}")

        return 0

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user", file=sys.stderr)
        return 130

    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        if not args.quiet:
            import traceback
            print("\nFull traceback:", file=sys.stderr)
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
