#!/usr/bin/env python3
"""
Debug script to visualize sprite frame extraction
"""

from sprite_processing.sprite_sheet_analyzer import SpriteSheetAnalyzer
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from dotenv import load_dotenv
import sys

load_dotenv()


def visualize_frame_extraction(sprite_path: str, output_path: str = "debug_frames.png"):
    """
    Visualize how frames are being extracted from a sprite sheet
    """
    sprite_path = Path(sprite_path)

    print(f"🔍 Debugging sprite extraction for: {sprite_path.name}\n")

    analyzer = SpriteSheetAnalyzer()

    # Analyze layout
    print("📊 Analyzing layout...")
    layout_info = analyzer.analyze_sprite_sheet_layout(sprite_path)

    print(f"  Layout type: {layout_info['layout_type']}")
    print(f"  Grid: {layout_info['rows']} rows × {layout_info['columns']} columns")
    print(f"  Total frames: {layout_info['total_frames']}")
    print(f"  Frame dimensions: {layout_info['frame_width']}×{layout_info['frame_height']}px")
    print(f"  Explanation: {layout_info['explanation']}\n")

    # Load original sprite sheet
    sprite_img = Image.open(sprite_path)
    print(f"📐 Original image size: {sprite_img.size}")

    # Create a copy with grid overlay
    debug_img = sprite_img.copy().convert('RGBA')
    draw = ImageDraw.Draw(debug_img)

    # Draw grid based on detected layout
    rows = layout_info['rows']
    cols = layout_info['columns']
    frame_w = layout_info['frame_width']
    frame_h = layout_info['frame_height']

    print(f"\n🎯 Drawing grid overlay...")
    print(f"  Expected grid cells: {rows}×{cols}")
    print(f"  Cell size: {frame_w}×{frame_h}px\n")

    # Draw vertical lines
    for col in range(cols + 1):
        x = col * frame_w
        draw.line([(x, 0), (x, sprite_img.height)], fill=(255, 0, 0, 255), width=2)

    # Draw horizontal lines
    for row in range(rows + 1):
        y = row * frame_h
        draw.line([(0, y), (sprite_img.width, y)], fill=(255, 0, 0, 255), width=2)

    # Label each frame
    for row in range(rows):
        for col in range(cols):
            frame_num = row * cols + col
            x = col * frame_w + 5
            y = row * frame_h + 5
            draw.text((x, y), f"F{frame_num}", fill=(255, 255, 0, 255))

    # Save debug image
    debug_img.save(output_path)
    print(f"✓ Debug visualization saved: {output_path}")

    # Extract frames
    print(f"\n✂️  Extracting frames...")
    frames = analyzer.extract_frames_from_grid(
        sprite_path,
        rows=rows,
        columns=cols,
        frame_width=frame_w,
        frame_height=frame_h
    )

    print(f"✓ Extracted {len(frames)} frames")

    # Save individual frames for inspection
    frames_dir = Path("debug_frames")
    frames_dir.mkdir(exist_ok=True)

    for i, frame in enumerate(frames):
        frame_path = frames_dir / f"frame_{i:02d}.png"
        frame.save(frame_path)

    print(f"✓ Individual frames saved to: {frames_dir}/")

    # Create horizontal strip
    from sprite_processing.sprite_sheet_builder import SpriteSheetBuilder
    builder = SpriteSheetBuilder()

    horizontal_sheet, metadata = builder.create_horizontal_sheet(
        frames=frames,
        frame_width=frame_w,
        frame_height=frame_h,
        spacing=0
    )

    horizontal_path = "debug_horizontal.png"
    horizontal_sheet.save(horizontal_path)
    print(f"✓ Horizontal strip saved: {horizontal_path}")

    print(f"\n📊 Summary:")
    print(f"  Original: {sprite_img.size} ({layout_info['layout_type']})")
    print(f"  Horizontal: {horizontal_sheet.size} (1×{len(frames)})")
    print(f"  Frame size: {frame_w}×{frame_h}px")
    print(f"\n💡 Check the debug images to see if frames are extracted correctly!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_sprite_extraction.py <sprite_sheet_path>")
        sys.exit(1)

    visualize_frame_extraction(sys.argv[1])
