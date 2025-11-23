#!/usr/bin/env python3
"""
CLI tool for sprite processing
Removes backgrounds, creates sprite sheets, and generates Phaser.js configs
"""

import argparse
import sys
from pathlib import Path
from PIL import Image

from .background_remover import BackgroundRemover
from .sprite_sheet_builder import SpriteSheetBuilder
from .phaser_config import PhaserConfigGenerator


def process_sprites(args):
    """Process sprites: remove background and create sprite sheet"""

    # Initialize processors
    bg_remover = BackgroundRemover(threshold=args.threshold)
    sheet_builder = SpriteSheetBuilder()
    phaser_gen = PhaserConfigGenerator()

    # Load images
    print(f"Loading {len(args.images)} image(s)...")
    image_paths = [Path(p) for p in args.images]

    # Check all images exist
    for img_path in image_paths:
        if not img_path.exists():
            print(f"Error: Image not found: {img_path}")
            sys.exit(1)

    # Process sprites (remove backgrounds)
    print("Removing backgrounds...")
    processed_frames = []

    for i, img_path in enumerate(image_paths):
        print(f"  Processing frame {i + 1}/{len(image_paths)}: {img_path.name}")
        frame = bg_remover.process_sprite(
            img_path,
            output_size=(args.frame_width, args.frame_height) if args.frame_width and args.frame_height else None,
            auto_crop_enabled=not args.no_crop,
            crop_padding=args.crop_padding
        )
        processed_frames.append(frame)

    # Create sprite sheet
    print("\nCreating sprite sheet...")
    if args.layout == 'horizontal':
        sprite_sheet, metadata = sheet_builder.create_horizontal_sheet(
            processed_frames,
            spacing=args.spacing
        )
    else:
        sprite_sheet, metadata = sheet_builder.create_grid_sheet(
            processed_frames,
            columns=args.columns,
            spacing=args.spacing
        )

    # Save sprite sheet
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Saving sprite sheet to: {output_path}")
    sheet_builder.save_sprite_sheet(
        sprite_sheet,
        metadata,
        output_path,
        save_metadata=True
    )

    print(f"✓ Sprite sheet saved: {output_path}")
    print(f"✓ Metadata saved: {output_path.with_suffix('.json')}")

    # Generate Phaser.js config if requested
    if args.generate_phaser:
        print("\nGenerating Phaser.js configuration...")
        phaser_output = phaser_gen.save_phaser_config(
            metadata,
            output_path.parent / args.phaser_key,
            texture_key=args.phaser_key,
            sprite_sheet_path=args.phaser_path or f"assets/sprites/{output_path.name}",
            generate_code=True
        )

        print(f"✓ Phaser config saved: {phaser_output['config_file']}")
        print(f"✓ Phaser code saved: {phaser_output['code_file']}")

    # Print summary
    print("\n" + "="*60)
    print("Summary:")
    print(f"  Frames processed: {metadata['frame_count']}")
    print(f"  Frame size: {metadata['frame_width']}x{metadata['frame_height']}")
    print(f"  Sheet size: {metadata['sheet_width']}x{metadata['sheet_height']}")
    print(f"  Layout: {args.layout}")
    if args.layout == 'grid':
        print(f"  Grid: {metadata['columns']}x{metadata['rows']}")
    print("="*60)


def main():
    """Main CLI entry point"""

    parser = argparse.ArgumentParser(
        description='Process sprite images for game development (Phaser.js)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process walk cycle frames into horizontal sprite sheet
  %(prog)s frame1.png frame2.png frame3.png -o output/walk.png

  # Create grid sprite sheet with Phaser.js config
  %(prog)s *.png -o sprites/character.png --layout grid --columns 4 --generate-phaser

  # Process with custom frame size and no cropping
  %(prog)s frame*.png -o output.png --frame-width 64 --frame-height 64 --no-crop

  # Generate with specific Phaser.js settings
  %(prog)s walk*.png -o character.png --generate-phaser --phaser-key player --phaser-path assets/player.png
        """
    )

    # Input/Output
    parser.add_argument('images', nargs='+', help='Input image files')
    parser.add_argument('-o', '--output', required=True, help='Output sprite sheet path')

    # Background removal options
    parser.add_argument('--threshold', type=int, default=240,
                       help='White background threshold (0-255, default: 240)')
    parser.add_argument('--no-crop', action='store_true',
                       help='Disable auto-cropping of transparent borders')
    parser.add_argument('--crop-padding', type=int, default=5,
                       help='Padding around cropped content (default: 5)')

    # Frame sizing
    parser.add_argument('--frame-width', type=int,
                       help='Fixed frame width (optional)')
    parser.add_argument('--frame-height', type=int,
                       help='Fixed frame height (optional)')

    # Sprite sheet layout
    parser.add_argument('--layout', choices=['horizontal', 'grid'], default='horizontal',
                       help='Sprite sheet layout (default: horizontal)')
    parser.add_argument('--columns', type=int, default=8,
                       help='Number of columns for grid layout (default: 8)')
    parser.add_argument('--spacing', type=int, default=0,
                       help='Spacing between frames in pixels (default: 0)')

    # Phaser.js options
    parser.add_argument('--generate-phaser', action='store_true',
                       help='Generate Phaser.js configuration files')
    parser.add_argument('--phaser-key', default='character',
                       help='Phaser texture key (default: character)')
    parser.add_argument('--phaser-path', help='Path for Phaser to load sprite sheet')

    args = parser.parse_args()

    # Validate
    if args.frame_width and args.frame_width <= 0:
        parser.error("Frame width must be positive")
    if args.frame_height and args.frame_height <= 0:
        parser.error("Frame height must be positive")
    if args.columns <= 0:
        parser.error("Columns must be positive")

    try:
        process_sprites(args)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
