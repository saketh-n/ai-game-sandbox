#!/usr/bin/env python3
"""
Visualize sprite sheet extraction step-by-step
"""

from sprite_processing.sprite_sheet_analyzer import SpriteSheetAnalyzer
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from dotenv import load_dotenv
import sys

load_dotenv()


def visualize_extraction(sprite_url_or_path: str):
    """
    Download and visualize the sprite extraction process
    """
    import tempfile
    import httpx

    print(f"🔍 Visualizing sprite extraction...\n")

    # Download if URL, otherwise use local path
    if sprite_url_or_path.startswith('http'):
        print(f"📥 Downloading sprite sheet from URL...")
        with httpx.Client() as client:
            response = client.get(sprite_url_or_path)
            response.raise_for_status()

        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as f:
            f.write(response.content)
            sprite_path = Path(f.name)
        print(f"  ✓ Downloaded to: {sprite_path}")
    else:
        sprite_path = Path(sprite_url_or_path)

    analyzer = SpriteSheetAnalyzer()

    # Analyze layout
    print("\n📊 Step 1: Analyzing layout...")
    layout_info = analyzer.analyze_sprite_sheet_layout(sprite_path)
    print(f"  Layout: {layout_info['layout_type']}")
    print(f"  Grid: {layout_info['rows']}×{layout_info['columns']}")
    print(f"  Total frames: {layout_info['total_frames']}")

    # Load sprite sheet
    sprite_sheet = Image.open(sprite_path).convert('RGBA')
    rows = layout_info['rows']
    cols = layout_info['columns']

    cell_width = sprite_sheet.width // cols
    cell_height = sprite_sheet.height // rows

    print(f"\n📐 Step 2: Grid cell size: {cell_width}×{cell_height}px")

    # Create visualization canvas
    vis_width = sprite_sheet.width * 2 + 40
    vis_height = sprite_sheet.height * 2 + 100
    visualization = Image.new('RGB', (vis_width, vis_height), (40, 40, 40))
    draw = ImageDraw.Draw(visualization)

    # Draw original sprite sheet with grid overlay
    draw.text((10, 10), "Original with Grid", fill=(255, 255, 255))
    visualization.paste(sprite_sheet, (10, 40), sprite_sheet)

    # Draw grid lines
    for row in range(rows + 1):
        y = 40 + row * cell_height
        draw.line([(10, y), (10 + sprite_sheet.width, y)], fill=(255, 0, 0), width=2)

    for col in range(cols + 1):
        x = 10 + col * cell_width
        draw.line([(x, 40), (x, 40 + sprite_sheet.height)], fill=(255, 0, 0), width=2)

    # Extract frames with visualization
    print(f"\n✂️  Step 3: Extracting frames with individual bounds...")

    import numpy as np

    extracted_frames = []
    frame_y_offset = 40 + sprite_sheet.height + 60

    for row in range(rows):
        for col in range(cols):
            frame_num = row * cols + col

            # Extract grid cell
            x = col * cell_width
            y = row * cell_height
            cell = sprite_sheet.crop((x, y, x + cell_width, y + cell_height))

            # Find content bounds
            alpha = np.array(cell)[:, :, 3]
            rows_with_content = np.where(alpha.max(axis=1) > 10)[0]
            cols_with_content = np.where(alpha.max(axis=0) > 10)[0]

            if len(rows_with_content) > 0 and len(cols_with_content) > 0:
                left = cols_with_content[0]
                right = cols_with_content[-1] + 1
                top = rows_with_content[0]
                bottom = rows_with_content[-1] + 1

                # Draw bounding box on original
                box_x1 = 10 + x + left
                box_y1 = 40 + y + top
                box_x2 = 10 + x + right
                box_y2 = 40 + y + bottom
                draw.rectangle([box_x1, box_y1, box_x2, box_y2], outline=(0, 255, 0), width=2)
                draw.text((box_x1 + 2, box_y1 + 2), f"F{frame_num}", fill=(0, 255, 0))

                # Crop to content
                cropped = cell.crop((left, top, right, bottom))

                print(f"  Frame {frame_num}: bounds=({left},{top},{right},{bottom}) size={cropped.width}×{cropped.height}px")

                extracted_frames.append(cropped)
            else:
                print(f"  Frame {frame_num}: No content detected")
                extracted_frames.append(cell)

    # Draw extracted frames
    print(f"\n🎨 Step 4: Visualizing extracted frames...")
    draw.text((sprite_sheet.width + 30, 10), "Extracted Frames", fill=(255, 255, 255))

    x_offset = sprite_sheet.width + 30
    y_offset = 40

    for i, frame in enumerate(extracted_frames):
        # Paste frame
        visualization.paste(frame, (x_offset, y_offset), frame)

        # Draw frame number
        draw.text((x_offset, y_offset), f"F{i}", fill=(255, 255, 0))

        # Draw border
        draw.rectangle(
            [x_offset, y_offset, x_offset + frame.width, y_offset + frame.height],
            outline=(100, 100, 100),
            width=1
        )

        x_offset += frame.width + 5

        if (i + 1) % cols == 0:
            x_offset = sprite_sheet.width + 30
            y_offset += max(f.height for f in extracted_frames[i - cols + 1:i + 1]) + 5

    # Save visualization
    output_path = "sprite_extraction_debug.png"
    visualization.save(output_path)
    print(f"\n✅ Visualization saved to: {output_path}")

    # Also create horizontal strip
    print(f"\n🔨 Step 5: Creating horizontal strip...")
    frames, frame_w, frame_h = analyzer.extract_frames_smart(
        sprite_path,
        rows=rows,
        columns=cols
    )

    # Create horizontal visualization
    horizontal_width = frame_w * len(frames) + 20
    horizontal_height = frame_h + 60
    horizontal_vis = Image.new('RGB', (horizontal_width, horizontal_height), (40, 40, 40))
    h_draw = ImageDraw.Draw(horizontal_vis)

    h_draw.text((10, 10), f"Final Horizontal Strip ({len(frames)} frames @ {frame_w}×{frame_h}px)", fill=(255, 255, 255))

    x_pos = 10
    for i, frame in enumerate(frames):
        horizontal_vis.paste(frame, (x_pos, 40), frame)
        h_draw.rectangle([x_pos, 40, x_pos + frame_w, 40 + frame_h], outline=(100, 100, 100), width=1)
        h_draw.text((x_pos + 2, 42), f"{i}", fill=(255, 255, 0))
        x_pos += frame_w

    horizontal_output = "sprite_horizontal_debug.png"
    horizontal_vis.save(horizontal_output)
    print(f"✅ Horizontal strip saved to: {horizontal_output}")

    print(f"\n💡 Open these files to inspect the extraction:")
    print(f"   1. {output_path} - Shows grid + bounds + extracted frames")
    print(f"   2. {horizontal_output} - Shows final horizontal strip")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python visualize_sprite_extraction.py <sprite_url_or_path>")
        print("\nExample:")
        print("  python visualize_sprite_extraction.py https://example.com/sprite.png")
        print("  python visualize_sprite_extraction.py ./local_sprite.png")
        sys.exit(1)

    visualize_extraction(sys.argv[1])
