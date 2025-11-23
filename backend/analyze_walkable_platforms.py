#!/usr/bin/env python3
"""
Accurate Walkable Platform Analysis
Identifies ONLY green grass walkable surfaces, excludes decorative elements
"""

from PIL import Image, ImageDraw
import json


def analyze_walkable_platforms(image_path: str):
    """
    Analyze pixel art background to identify ONLY walkable green grass platforms.

    Rules:
    - Only green grass surfaces are walkable
    - Trees are decorative (no collision)
    - Fences are decorative (no collision)
    - Gaps between platforms require jumping
    """

    img = Image.open(image_path)
    width, height = img.size

    print(f"Background size: {width}x{height}")

    # Identified walkable grass platforms ONLY
    # These are precise based on visual analysis of green grass surfaces

    platforms = [
        # Bottom ground - green grass platform (fence is decorative, sits on top)
        {
            "name": "Bottom Ground",
            "x": 0,
            "y": 740,  # Top of green grass
            "width": width,
            "height": 28,  # Just the grass layer
            "walkable": True
        },

        # Left floating island - top green grass only
        {
            "name": "Left Island",
            "x": 0,
            "y": 593,  # Top of green grass
            "width": 205,
            "height": 20,
            "walkable": True
        },

        # Middle-left small platform - green grass
        {
            "name": "Middle-Left Platform",
            "x": 215,
            "y": 668,  # Top of green grass
            "width": 158,
            "height": 20,
            "walkable": True
        },

        # Middle bridge area - green grass under/around fence
        # Note: Fence itself is NOT a collision object
        {
            "name": "Middle Bridge Platform",
            "x": 398,
            "y": 648,  # Top of green grass
            "width": 198,
            "height": 20,
            "walkable": True
        },

        # Right large island - green grass on top
        {
            "name": "Right Island",
            "x": 680,
            "y": 593,  # Top of green grass
            "width": 344,
            "height": 20,
            "walkable": True
        },
    ]

    # Calculate good spawn position - on bottom ground, clear of obstacles
    spawn_x = width // 2
    spawn_y = 640  # Well above bottom ground

    # Identify gaps (non-walkable areas that require jumping)
    gaps = [
        {"start_x": 205, "end_x": 215, "description": "Gap between left island and middle-left platform"},
        {"start_x": 373, "end_x": 398, "description": "Gap between middle-left and bridge"},
        {"start_x": 596, "end_x": 680, "description": "Gap between bridge and right island"},
    ]

    return {
        "width": width,
        "height": height,
        "platforms": platforms,
        "gaps": gaps,
        "spawn": {
            "x": spawn_x,
            "y": spawn_y
        },
        "notes": [
            "Trees are decorative only - no collision",
            "Fences are decorative only - no collision",
            "Only green grass surfaces are walkable",
            f"{len(gaps)} gaps require jumping between platforms"
        ]
    }


def visualize_walkable_platforms(image_path: str, analysis: dict, output_path: str):
    """Visualize ONLY walkable platforms and gaps"""

    img = Image.open(image_path).convert('RGBA')
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Draw walkable platforms in green
    for platform in analysis['platforms']:
        if platform.get('walkable'):
            x, y = platform['x'], platform['y']
            w, h = platform['width'], platform['height']

            # Draw platform
            draw.rectangle(
                [x, y, x + w, y + h],
                fill=(0, 255, 0, 120),
                outline=(0, 255, 0, 255),
                width=3
            )

            # Label
            draw.text((x + 5, y - 15), platform['name'], fill=(255, 255, 255, 255))

    # Draw gaps in red
    for gap in analysis['gaps']:
        x1, x2 = gap['start_x'], gap['end_x']
        draw.line([(x1, 650), (x2, 650)], fill=(255, 0, 0, 255), width=5)
        draw.text((x1, 630), "GAP", fill=(255, 0, 0, 255))

    # Draw spawn point
    spawn_x, spawn_y = analysis['spawn']['x'], analysis['spawn']['y']
    draw.ellipse(
        [spawn_x - 15, spawn_y - 15, spawn_x + 15, spawn_y + 15],
        fill=(255, 0, 255, 200),
        outline=(255, 255, 255, 255),
        width=2
    )
    draw.text((spawn_x + 20, spawn_y - 10), "SPAWN", fill=(255, 0, 255, 255))

    # Add notes
    y_offset = 20
    for note in analysis['notes']:
        draw.text((10, y_offset), f"• {note}", fill=(255, 255, 255, 255))
        y_offset += 20

    result = Image.alpha_composite(img, overlay)
    result.save(output_path)
    print(f"✓ Walkable platform visualization saved to: {output_path}")


if __name__ == "__main__":
    print("="*70)
    print("Walkable Platform Analysis")
    print("="*70)

    bg_path = "test_background.png"
    analysis = analyze_walkable_platforms(bg_path)

    print(f"\n📊 Analysis Results:")
    print(f"  Background: {analysis['width']}x{analysis['height']}")
    print(f"  Walkable platforms: {len(analysis['platforms'])}")
    print(f"  Gaps (require jumping): {len(analysis['gaps'])}")

    print(f"\n🟢 Walkable Green Grass Platforms:")
    for i, platform in enumerate(analysis['platforms'], 1):
        print(f"  {i}. {platform['name']:<25s} @ ({platform['x']:4d}, {platform['y']:3d}) - {platform['width']:3d}x{platform['height']:2d}")

    print(f"\n🔴 Gaps (Non-walkable areas):")
    for gap in analysis['gaps']:
        print(f"  • x={gap['start_x']}-{gap['end_x']}: {gap['description']}")

    print(f"\n🏁 Spawn Point: ({analysis['spawn']['x']}, {analysis['spawn']['y']})")

    print(f"\n📝 Important Notes:")
    for note in analysis['notes']:
        print(f"  • {note}")

    # Create visualization
    viz_path = "walkable_platforms_analysis.png"
    visualize_walkable_platforms(bg_path, analysis, viz_path)

    # Save for game generation
    with open("walkable_platforms.json", 'w') as f:
        json.dump(analysis, f, indent=2)

    print(f"\n✓ Analysis saved to: walkable_platforms.json")
    print("="*70)
