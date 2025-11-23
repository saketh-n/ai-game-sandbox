#!/usr/bin/env python3
"""
Unified Game Generator
Creates playable HTML5 platformer games from character sprites and background images
"""

from pathlib import Path
from typing import Optional, Dict, Any
import json
from PIL import Image
import anthropic
import os
from dotenv import load_dotenv

from sprite_processing.background_remover import BackgroundRemover
from sprite_processing.sprite_sheet_builder import SpriteSheetBuilder
from scene_builder.background_analyzer import BackgroundAnalyzer
from scene_builder.scene_generator import SceneGenerator
from scene_builder.web_exporter import WebGameExporter

load_dotenv()


class GameGenerator:
    """
    Orchestrates the complete pipeline from assets to playable game
    """

    def __init__(self, output_dir: str = "generated_game"):
        """
        Initialize game generator

        Args:
            output_dir: Directory where game files will be saved
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize processing modules
        self.bg_remover = BackgroundRemover()
        self.sprite_builder = SpriteSheetBuilder()
        self.bg_analyzer = BackgroundAnalyzer()
        self.scene_gen = SceneGenerator()
        self.web_exporter = WebGameExporter()

        # Initialize Anthropic client for VLM analysis (required)
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY required for platform detection. Set it in your .env file.")
        self.anthropic_client = anthropic.Anthropic(api_key=api_key)

    def analyze_walkable_platforms(self, background_path: Path) -> Dict[str, Any]:
        """
        Use VLM (Claude Sonnet 4.5) to identify walkable platforms in background

        Args:
            background_path: Path to background image

        Returns:
            Dictionary with platform data, gaps, and spawn point
        """
        print(f"\n🔍 Analyzing walkable platforms with Claude Vision API...")
        print(f"  Background: {background_path.name}")

        # Load and encode image
        img = Image.open(background_path)
        width, height = img.size
        print(f"  Dimensions: {width}x{height}px")

        # Convert image to base64 for Claude API
        import base64
        import io

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.standard_b64encode(buffer.getvalue()).decode('utf-8')

        # Create vision analysis prompt
        prompt = f"""Analyze this 2D platformer game background image ({width}x{height}px) and identify ONLY the walkable grass platforms where a character can stand.

IMPORTANT RULES:
- Only green grass surfaces are walkable
- Trees are decorative (NOT walkable)
- Fences are decorative (NOT walkable)
- Water/sky areas are NOT walkable
- Only detect solid horizontal platforms

For each walkable grass platform, provide:
1. A descriptive name
2. Position (x, y) - top-left corner in pixels
3. Dimensions (width, height) in pixels

Also identify:
- Gaps between platforms (where jumping is required)
- Best spawn point for the player character (on a safe platform)

Return your analysis as a JSON object with this exact structure:
{{
  "platforms": [
    {{"name": "Platform Name", "x": 0, "y": 740, "width": 1024, "height": 28, "walkable": true}},
    ...
  ],
  "gaps": [
    {{"description": "Gap description", "from_platform": "Platform A", "to_platform": "Platform B", "width": 50}},
    ...
  ],
  "spawn": {{"x": 512, "y": 640}},
  "notes": ["Tree decorations have no collision", ...]
}}

Only return the JSON, no other text."""

        # Call Claude Vision API
        print(f"  Calling Claude Sonnet 4.5 for analysis...")

        response = self.anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        # Parse response
        response_text = response.content[0].text.strip()

        # Remove markdown code fences if present
        if response_text.startswith("```"):
            lines = response_text.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = '\n'.join(lines).strip()

        analysis_data = json.loads(response_text)

        # Add image dimensions
        analysis_data["width"] = width
        analysis_data["height"] = height

        print(f"  ✓ Found {len(analysis_data['platforms'])} walkable platforms")
        print(f"  ✓ Identified {len(analysis_data['gaps'])} gaps requiring jumps")
        print(f"  ✓ Spawn point: ({analysis_data['spawn']['x']}, {analysis_data['spawn']['y']})")

        return analysis_data

    def process_character_sprite(
        self,
        sprite_path: Path,
        num_frames: int = 8,
        frame_width: Optional[int] = None,
        frame_height: Optional[int] = None
    ) -> tuple[Path, Dict[str, Any]]:
        """
        Process character sprite sheet - removes background and detects frame dimensions

        Args:
            sprite_path: Path to sprite sheet image
            num_frames: Number of animation frames
            frame_width: Width of each frame (auto-detected if None)
            frame_height: Height of each frame (auto-detected if None)

        Returns:
            Tuple of (processed_sprite_path, sprite_config)
        """
        print(f"\n🎨 Processing character sprite {sprite_path.name}...")

        # Load sprite sheet
        sprite_img = Image.open(sprite_path)
        sheet_width, sheet_height = sprite_img.size
        print(f"  Original size: {sheet_width}x{sheet_height}px")

        # Remove white background
        print(f"  Removing background...")
        processed_img = self.bg_remover.remove_background(
            sprite_img,
            background_color=(255, 255, 255),  # White background
            tolerance=40
        )

        # Auto-crop to remove excess transparent space
        processed_img = self.bg_remover.auto_crop(processed_img, padding=5)
        cropped_width, cropped_height = processed_img.size
        print(f"  ✓ Background removed and cropped: {cropped_width}x{cropped_height}px")

        # Auto-detect frame dimensions if not provided
        if frame_width is None:
            frame_width = cropped_width // num_frames
        if frame_height is None:
            frame_height = cropped_height

        print(f"  ✓ Frame size: {frame_width}x{frame_height}px")
        print(f"  ✓ Number of frames: {num_frames}")

        # Save processed sprite
        processed_path = self.output_dir / "assets" / f"processed_{sprite_path.name}"
        processed_path.parent.mkdir(parents=True, exist_ok=True)
        processed_img.save(processed_path)
        print(f"  ✓ Processed sprite saved: {processed_path.name}")

        sprite_config = {
            "sprite_path": str(processed_path),
            "frame_width": frame_width,
            "frame_height": frame_height,
            "num_frames": num_frames
        }

        return processed_path, sprite_config

    def generate_game(
        self,
        character_sprite: str,
        background_image: str,
        num_frames: int = 8,
        game_name: str = "PlatformerGame",
        player_config: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Generate complete playable game from assets

        Args:
            character_sprite: Path to character sprite sheet
            background_image: Path to background image
            num_frames: Number of animation frames in sprite sheet
            game_name: Name for the generated game
            player_config: Optional player physics configuration

        Returns:
            Path to generated game.html
        """
        print("=" * 70)
        print(f"🎮 Generating {game_name}")
        print("=" * 70)

        # Convert to Path objects
        char_path = Path(character_sprite)
        bg_path = Path(background_image)

        # Validate inputs
        if not char_path.exists():
            raise FileNotFoundError(f"Character sprite not found: {char_path}")
        if not bg_path.exists():
            raise FileNotFoundError(f"Background image not found: {bg_path}")

        # Process assets
        processed_sprite_path, sprite_config = self.process_character_sprite(
            char_path,
            num_frames=num_frames
        )

        platform_analysis = self.analyze_walkable_platforms(bg_path)

        # Set up default player configuration
        if player_config is None:
            player_config = {
                "walk_speed": 180,
                "jump_velocity": -380,
                "max_jumps": 2
            }

        # Create scene configuration
        scene_config = {
            "name": game_name,
            "background": {
                "path": str(bg_path),
                "width": platform_analysis["width"],
                "height": platform_analysis["height"]
            },
            "character": {
                "sprite_path": str(processed_sprite_path),
                "frame_width": sprite_config["frame_width"],
                "frame_height": sprite_config["frame_height"],
                "num_frames": sprite_config["num_frames"],
                "spawn_x": platform_analysis["spawn"]["x"],
                "spawn_y": platform_analysis["spawn"]["y"]
            },
            "physics": {
                "gravity": 600,
                "platforms": platform_analysis["platforms"],
                "bounds": {
                    "x": 0,
                    "y": 0,
                    "width": platform_analysis["width"],
                    "height": platform_analysis["height"]
                }
            },
            "player": player_config,
            "analysis": platform_analysis
        }

        # Save configuration
        print(f"\n💾 Saving game configuration...")
        config_path = self.output_dir / "scene_config.json"
        self.scene_gen.save_scene_config(scene_config, config_path)
        print(f"  ✓ Config saved to {config_path}")

        # Copy background to output directory
        print(f"\n📦 Copying background...")
        assets_dir = self.output_dir / "assets"
        assets_dir.mkdir(exist_ok=True)

        bg_dest = assets_dir / bg_path.name
        Image.open(bg_path).save(bg_dest)
        print(f"  ✓ Background: {bg_dest.name}")
        print(f"  ✓ Character sprite already processed and saved")

        # Export game
        print(f"\n🔨 Generating game files...")
        game_path = self.output_dir / "game.html"
        self.web_exporter.export_game(scene_config, game_path, embed_assets=False)
        print(f"  ✓ Game HTML: {game_path}")

        # Create run script
        run_script = self.output_dir / "run_game.py"
        self._create_run_script(run_script)
        print(f"  ✓ Run script: {run_script}")

        # Summary
        print("\n" + "=" * 70)
        print(f"✅ {game_name} Generated Successfully!")
        print("=" * 70)

        print(f"\n🎯 Game Features:")
        print(f"  ✓ {len(platform_analysis['platforms'])} walkable platforms")
        print(f"  ✓ {len(platform_analysis['gaps'])} gaps requiring jumps")
        print(f"  ✓ Double jump mechanics")
        print(f"  ✓ Responsive canvas sizing")
        print(f"  ✓ {num_frames}-frame character animation")

        print(f"\n🎮 To Play:")
        print(f"    cd {self.output_dir} && python3 run_game.py")
        print(f"    OR open http://localhost:8080/game.html")

        print("\n💡 Controls:")
        print("  ← → : Move left/right")
        print("  SPACE : Jump (double jump!)")
        print("  R : Reset position")

        print("=" * 70)

        return game_path

    def generate_game_html_with_embedded_assets(
        self,
        character_sprite: str,
        background_image: str,
        num_frames: int = 8,
        game_name: str = "PlatformerGame",
        player_config: Optional[Dict[str, Any]] = None
    ) -> tuple[str, Dict[str, Any]]:
        """
        Generate game HTML with base64-embedded assets for iframe embedding

        Args:
            character_sprite: Path to character sprite sheet
            background_image: Path to background image
            num_frames: Number of animation frames
            game_name: Name for the generated game
            player_config: Optional player physics configuration

        Returns:
            Tuple of (game_html_string, scene_config_dict)
        """
        print("=" * 70)
        print(f"🎮 Generating {game_name} with embedded assets")
        print("=" * 70)

        # Convert to Path objects
        char_path = Path(character_sprite)
        bg_path = Path(background_image)

        # Validate inputs
        if not char_path.exists():
            raise FileNotFoundError(f"Character sprite not found: {char_path}")
        if not bg_path.exists():
            raise FileNotFoundError(f"Background image not found: {bg_path}")

        # Process assets
        processed_sprite_path, sprite_config = self.process_character_sprite(
            char_path,
            num_frames=num_frames
        )

        platform_analysis = self.analyze_walkable_platforms(bg_path)

        # Set up default player configuration
        if player_config is None:
            player_config = {
                "walk_speed": 180,
                "jump_velocity": -380,
                "max_jumps": 2
            }

        # Convert images to base64
        import base64

        print(f"\n📦 Encoding assets as base64...")
        with open(bg_path, 'rb') as f:
            bg_base64 = base64.b64encode(f.read()).decode('utf-8')
        bg_data_url = f"data:image/png;base64,{bg_base64}"
        print(f"  ✓ Background encoded")

        with open(processed_sprite_path, 'rb') as f:
            sprite_base64 = base64.b64encode(f.read()).decode('utf-8')
        sprite_data_url = f"data:image/png;base64,{sprite_base64}"
        print(f"  ✓ Character sprite encoded")

        # Create scene configuration with data URLs
        scene_config = {
            "name": game_name,
            "background": {
                "path": bg_data_url,  # Use data URL instead of file path
                "width": platform_analysis["width"],
                "height": platform_analysis["height"]
            },
            "character": {
                "sprite_path": sprite_data_url,  # Use data URL instead of file path
                "frame_width": sprite_config["frame_width"],
                "frame_height": sprite_config["frame_height"],
                "num_frames": sprite_config["num_frames"],
                "spawn_x": platform_analysis["spawn"]["x"],
                "spawn_y": platform_analysis["spawn"]["y"]
            },
            "physics": {
                "gravity": 600,
                "platforms": platform_analysis["platforms"],
                "bounds": {
                    "x": 0,
                    "y": 0,
                    "width": platform_analysis["width"],
                    "height": platform_analysis["height"]
                }
            },
            "player": player_config,
            "analysis": platform_analysis
        }

        # Generate HTML with embedded assets
        print(f"\n🔨 Generating HTML with embedded assets...")
        game_html = self.web_exporter._generate_html(
            scene_config,
            bg_data_url,  # Pass data URL
            sprite_data_url  # Pass data URL
        )

        print(f"  ✓ Game HTML generated: {len(game_html)} characters")
        print("=" * 70)

        return game_html, scene_config

    def generate_game_html_with_urls(
        self,
        character_sprite_path: str,
        character_sprite_url: str,
        background_image_path: str,
        background_image_url: str,
        num_frames: int = 8,
        game_name: str = "PlatformerGame",
        player_config: Optional[Dict[str, Any]] = None
    ) -> tuple[str, Dict[str, Any]]:
        """
        Generate game HTML using original image URLs (for Phaser compatibility)

        Downloads images for analysis/processing, but uses original URLs in HTML
        since Phaser doesn't support data URIs.

        Args:
            character_sprite_path: Local path to downloaded character sprite
            character_sprite_url: Original URL to character sprite
            background_image_path: Local path to downloaded background
            background_image_url: Original URL to background
            num_frames: Number of animation frames
            game_name: Name for the generated game
            player_config: Optional player physics configuration

        Returns:
            Tuple of (game_html_string, scene_config_dict)
        """
        print("=" * 70)
        print(f"🎮 Generating {game_name} with URL references")
        print("=" * 70)

        # Convert to Path objects
        char_path = Path(character_sprite_path)
        bg_path = Path(background_image_path)

        # Process character sprite locally (remove background, get dimensions)
        processed_sprite_path, sprite_config = self.process_character_sprite(
            char_path,
            num_frames=num_frames
        )

        # Analyze background locally with Claude Vision
        platform_analysis = self.analyze_walkable_platforms(bg_path)

        # Set up default player configuration
        if player_config is None:
            player_config = {
                "walk_speed": 180,
                "jump_velocity": -380,
                "max_jumps": 2
            }

        # Convert processed sprite to base64 for embedding
        import base64
        print(f"\n📦 Encoding processed sprite as base64...")
        with open(processed_sprite_path, 'rb') as f:
            sprite_base64 = base64.b64encode(f.read()).decode('utf-8')
        processed_sprite_data_url = f"data:image/png;base64,{sprite_base64}"
        print(f"  ✓ Processed sprite encoded ({len(sprite_base64)} bytes)")

        # Create scene configuration
        scene_config = {
            "name": game_name,
            "background": {
                "path": background_image_url,  # Use original URL for background
                "width": platform_analysis["width"],
                "height": platform_analysis["height"]
            },
            "character": {
                "sprite_path": processed_sprite_data_url,  # Use data URL for processed sprite
                "sprite_path_original": character_sprite_url,  # Keep original for reference
                "frame_width": sprite_config["frame_width"],
                "frame_height": sprite_config["frame_height"],
                "num_frames": sprite_config["num_frames"],
                "spawn_x": platform_analysis["spawn"]["x"],
                "spawn_y": platform_analysis["spawn"]["y"]
            },
            "physics": {
                "gravity": 600,
                "platforms": platform_analysis["platforms"],
                "bounds": {
                    "x": 0,
                    "y": 0,
                    "width": platform_analysis["width"],
                    "height": platform_analysis["height"]
                }
            },
            "player": player_config,
            "analysis": platform_analysis
        }

        # Generate HTML with URLs (background URL + sprite data URI)
        print(f"\n🔨 Generating HTML with URL references...")
        game_html = self.web_exporter._generate_html(
            scene_config,
            background_image_url,  # Pass original URL for background
            processed_sprite_data_url  # Pass data URL for processed sprite
        )

        print(f"  ✓ Game HTML generated: {len(game_html)} characters")
        print(f"  ✓ Using original image URLs (Phaser compatible)")
        print("=" * 70)

        return game_html, scene_config

    def _create_run_script(self, output_path: Path):
        """Create a simple HTTP server script to run the game"""
        script_content = '''#!/usr/bin/env python3
"""
Simple HTTP server to run the game
This avoids CORS issues when loading local files
"""

import http.server
import socketserver
import webbrowser
import os
from pathlib import Path

PORT = 8080

# Change to the directory containing this script
os.chdir(Path(__file__).parent)

Handler = http.server.SimpleHTTPRequestHandler

print("=" * 70)
print("🎮 Platformer Game")
print("=" * 70)
print(f"\\n🌐 Starting server at http://localhost:{PORT}")
print(f"📁 Serving files from: {Path.cwd()}")
print(f"\\n🎯 Opening game in your browser...")
print(f"\\n⚠️  Press Ctrl+C to stop the server when you're done")
print("=" * 70 + "\\n")

# Open browser after a short delay
import threading
def open_browser():
    import time
    time.sleep(1)
    webbrowser.open(f'http://localhost:{PORT}/game.html')

threading.Thread(target=open_browser, daemon=True).start()

# Start server
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\n\\n✅ Server stopped. Thanks for playing!")
'''
        output_path.write_text(script_content)
        output_path.chmod(0o755)  # Make executable


def main():
    """CLI entry point for game generation"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate playable HTML5 platformer game from assets"
    )
    parser.add_argument(
        "--character",
        "-c",
        required=True,
        help="Path to character sprite sheet"
    )
    parser.add_argument(
        "--background",
        "-b",
        required=True,
        help="Path to background image"
    )
    parser.add_argument(
        "--frames",
        "-f",
        type=int,
        default=8,
        help="Number of animation frames (default: 8)"
    )
    parser.add_argument(
        "--output",
        "-o",
        default="generated_game",
        help="Output directory (default: generated_game)"
    )
    parser.add_argument(
        "--name",
        "-n",
        default="PlatformerGame",
        help="Game name (default: PlatformerGame)"
    )

    args = parser.parse_args()

    # Generate game
    generator = GameGenerator(output_dir=args.output)
    game_path = generator.generate_game(
        character_sprite=args.character,
        background_image=args.background,
        num_frames=args.frames,
        game_name=args.name
    )

    print(f"\n✨ Game ready at: {game_path}")


if __name__ == "__main__":
    main()
