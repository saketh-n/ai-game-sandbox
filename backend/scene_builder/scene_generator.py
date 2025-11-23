"""
Scene Generator
Combines background and character into a playable scene configuration
"""

from PIL import Image
from typing import Dict, Union, Optional
from pathlib import Path
import json

from .background_analyzer import BackgroundAnalyzer


class SceneGenerator:
    """Generates complete game scenes"""

    def __init__(self):
        """Initialize scene generator"""
        self.analyzer = BackgroundAnalyzer()

    def create_scene(
        self,
        background_path: Union[str, Path],
        character_sprite_path: Union[str, Path],
        character_frame_width: int,
        character_frame_height: int,
        num_frames: int = 8,
        scene_name: str = "GameScene"
    ) -> Dict:
        """
        Create a complete scene configuration

        Args:
            background_path: Path to background image
            character_sprite_path: Path to character sprite sheet
            character_frame_width: Width of each character frame
            character_frame_height: Height of each character frame
            num_frames: Number of animation frames
            scene_name: Name of the scene

        Returns:
            Scene configuration dict
        """
        # Analyze background
        print(f"Analyzing background: {background_path}")
        analysis = self.analyzer.analyze_ground_level(background_path)

        # Create platforms from analysis
        platforms = self.analyzer.create_ground_platform(analysis)

        # Get background dimensions
        bg_img = Image.open(background_path)
        bg_width, bg_height = bg_img.size

        # Calculate spawn position (center of first walkable region)
        spawn_x = bg_width // 2
        spawn_y = analysis['average_ground'] - character_frame_height - 50

        if analysis['walkable_regions']:
            first_region = analysis['walkable_regions'][0]
            spawn_x = (first_region['start_x'] + first_region['end_x']) // 2
            spawn_y = first_region['min_y'] - character_frame_height - 10

        # Create scene configuration
        scene_config = {
            'name': scene_name,
            'background': {
                'path': str(background_path),
                'width': bg_width,
                'height': bg_height
            },
            'character': {
                'sprite_path': str(character_sprite_path),
                'frame_width': character_frame_width,
                'frame_height': character_frame_height,
                'num_frames': num_frames,
                'spawn_x': spawn_x,
                'spawn_y': spawn_y
            },
            'physics': {
                'gravity': 800,
                'platforms': platforms,
                'bounds': {
                    'x': 0,
                    'y': 0,
                    'width': bg_width,
                    'height': bg_height
                }
            },
            'player': {
                'walk_speed': 200,
                'jump_velocity': -400,
                'max_jumps': 2  # Allow double jump
            },
            'analysis': analysis
        }

        return scene_config

    def save_scene_config(
        self,
        scene_config: Dict,
        output_path: Union[str, Path]
    ):
        """
        Save scene configuration to JSON file

        Args:
            scene_config: Scene configuration dict
            output_path: Output JSON file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert paths to strings for JSON serialization
        config_copy = scene_config.copy()

        with open(output_path, 'w') as f:
            json.dump(config_copy, f, indent=2)

        print(f"✓ Scene configuration saved to: {output_path}")

    def visualize_scene(
        self,
        scene_config: Dict,
        output_path: Optional[Union[str, Path]] = None
    ) -> Image.Image:
        """
        Create a visualization of the scene with platforms and spawn point

        Args:
            scene_config: Scene configuration
            output_path: Optional output path for visualization

        Returns:
            PIL Image with visualization
        """
        # Load background
        bg_path = scene_config['background']['path']
        visualization = self.analyzer.visualize_analysis(
            bg_path,
            scene_config['analysis']
        )

        # Add spawn point marker
        from PIL import ImageDraw
        draw = ImageDraw.Draw(visualization)

        spawn_x = scene_config['character']['spawn_x']
        spawn_y = scene_config['character']['spawn_y']
        char_width = scene_config['character']['frame_width']
        char_height = scene_config['character']['frame_height']

        # Draw character spawn box
        draw.rectangle([
            spawn_x - char_width // 2,
            spawn_y,
            spawn_x + char_width // 2,
            spawn_y + char_height
        ], outline=(255, 0, 255, 200), width=3)

        # Draw spawn point marker
        draw.ellipse([
            spawn_x - 5,
            spawn_y - 5,
            spawn_x + 5,
            spawn_y + 5
        ], fill=(255, 0, 255, 255))

        if output_path:
            visualization.save(output_path)

        return visualization
