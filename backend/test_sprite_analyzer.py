#!/usr/bin/env python3
"""
Test script for sprite sheet analyzer
"""

from sprite_processing.sprite_sheet_analyzer import SpriteSheetAnalyzer
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def main():
    print("🧪 Testing Sprite Sheet Analyzer\n")
    print("=" * 70)

    # Test with existing pineapple warrior (should be horizontal)
    test_sprite = Path("test_characeter_sprites.png")

    if not test_sprite.exists():
        print(f"❌ Test sprite not found: {test_sprite}")
        return

    analyzer = SpriteSheetAnalyzer()

    # Test 1: Analyze layout
    print("\n📊 Test 1: Analyzing sprite sheet layout...")
    print(f"   Input: {test_sprite.name}")

    layout_info = analyzer.analyze_sprite_sheet_layout(test_sprite)

    print(f"\n✓ Analysis complete:")
    print(f"   Layout type: {layout_info['layout_type']}")
    print(f"   Grid: {layout_info['rows']} rows × {layout_info['columns']} columns")
    print(f"   Total frames: {layout_info['total_frames']}")
    print(f"   Frame size: {layout_info['frame_width']}×{layout_info['frame_height']}px")
    print(f"   Explanation: {layout_info['explanation']}")

    # Test 2: Rearrange (should be no-op for horizontal)
    print("\n🔄 Test 2: Rearranging to horizontal...")
    output_path = Path("test_output_horizontal.png")

    result_path, result_info = analyzer.rearrange_to_horizontal(
        test_sprite,
        output_path,
        layout_info=layout_info
    )

    print(f"\n✓ Output saved: {result_path}")
    print(f"   Final layout: {result_info['rows']}×{result_info['columns']}")

    print("\n" + "=" * 70)
    print("✅ All tests passed!")

    # Instructions for grid sprite sheets
    print("\n💡 To test with a grid-based sprite sheet:")
    print("   1. Generate a sprite sheet in grid format (e.g., 2×4 or 4×2)")
    print("   2. Run: python test_sprite_analyzer.py <sprite_sheet.png>")
    print("   3. The analyzer will detect the grid and rearrange to horizontal")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Test with custom sprite sheet
        test_sprite = Path(sys.argv[1])
        output = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("rearranged_output.png")

        analyzer = SpriteSheetAnalyzer()
        print(f"📊 Analyzing: {test_sprite}")

        result_path, info = analyzer.rearrange_to_horizontal(test_sprite, output)

        print(f"\n✅ Success!")
        print(f"   Output: {result_path}")
        print(f"   Layout: {info}")
    else:
        main()
