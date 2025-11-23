"""
Phaser.js Configuration Generator
Generates Phaser.js-compatible animation configurations from sprite sheet metadata
"""

import json
from typing import Dict, Optional, Union
from pathlib import Path


class PhaserConfigGenerator:
    """Generates Phaser.js animation configurations"""

    def __init__(self):
        """Initialize Phaser config generator"""
        pass

    def generate_spritesheet_config(
        self,
        metadata: dict,
        texture_key: str = 'character',
        sprite_sheet_path: str = 'assets/sprites/character.png'
    ) -> dict:
        """
        Generate Phaser.js sprite sheet load configuration

        Args:
            metadata: Sprite sheet metadata from SpriteSheetBuilder
            texture_key: Key to reference this sprite sheet in Phaser
            sprite_sheet_path: Path to sprite sheet file (relative to game assets)

        Returns:
            Phaser.js load.spritesheet() config
        """
        config = {
            'key': texture_key,
            'url': sprite_sheet_path,
            'frameConfig': {
                'frameWidth': metadata['frame_width'],
                'frameHeight': metadata['frame_height'],
                'startFrame': 0,
                'endFrame': metadata['frame_count'] - 1
            }
        }

        if metadata.get('spacing', 0) > 0:
            config['frameConfig']['spacing'] = metadata['spacing']

        return config

    def generate_animation_config(
        self,
        animation_name: str,
        start_frame: int,
        end_frame: int,
        frame_rate: int = 10,
        repeat: int = -1,
        yoyo: bool = False
    ) -> dict:
        """
        Generate Phaser.js animation configuration

        Args:
            animation_name: Name of the animation
            start_frame: Starting frame index
            end_frame: Ending frame index
            frame_rate: Frames per second
            repeat: Number of times to repeat (-1 = infinite loop)
            yoyo: Whether to play in reverse after reaching end

        Returns:
            Phaser.js animation config
        """
        return {
            'key': animation_name,
            'frames': {
                'start': start_frame,
                'end': end_frame
            },
            'frameRate': frame_rate,
            'repeat': repeat,
            'yoyo': yoyo
        }

    def generate_character_animations(
        self,
        metadata: dict,
        texture_key: str = 'character',
        walk_frame_rate: int = 10,
        idle_frame_rate: int = 5
    ) -> Dict[str, dict]:
        """
        Generate standard character animations (walk-left, walk-right, idle)

        Args:
            metadata: Sprite sheet metadata
            texture_key: Texture key from spritesheet config
            walk_frame_rate: Frame rate for walking animations
            idle_frame_rate: Frame rate for idle animation

        Returns:
            Dict of animation configurations
        """
        animations = {}

        # Check if animations metadata exists
        if 'animations' in metadata:
            # Multi-animation sprite sheet
            for anim_name, anim_data in metadata['animations'].items():
                frame_rate = walk_frame_rate if 'walk' in anim_name.lower() else idle_frame_rate

                animations[anim_name] = {
                    'key': anim_name,
                    'frames': self._create_frame_array(
                        texture_key,
                        anim_data['start_frame'],
                        anim_data['end_frame']
                    ),
                    'frameRate': frame_rate,
                    'repeat': -1
                }
        else:
            # Single animation (assume walk cycle)
            total_frames = metadata['frame_count']

            # Walk right animation (all frames)
            animations['walk-right'] = {
                'key': 'walk-right',
                'frames': self._create_frame_array(texture_key, 0, total_frames - 1),
                'frameRate': walk_frame_rate,
                'repeat': -1
            }

            # Walk left animation (same frames, but sprite will be flipped)
            animations['walk-left'] = {
                'key': 'walk-left',
                'frames': self._create_frame_array(texture_key, 0, total_frames - 1),
                'frameRate': walk_frame_rate,
                'repeat': -1
            }

            # Idle animation (first frame only)
            animations['idle'] = {
                'key': 'idle',
                'frames': [{'key': texture_key, 'frame': 0}],
                'frameRate': idle_frame_rate,
                'repeat': -1
            }

        return animations

    def _create_frame_array(
        self,
        texture_key: str,
        start: int,
        end: int
    ) -> list:
        """
        Create Phaser frame array

        Args:
            texture_key: Sprite sheet texture key
            start: Start frame index
            end: End frame index

        Returns:
            List of frame objects
        """
        return [{'key': texture_key, 'frame': i} for i in range(start, end + 1)]

    def generate_phaser_code(
        self,
        metadata: dict,
        texture_key: str = 'character',
        sprite_sheet_path: str = 'assets/sprites/character.png',
        class_name: str = 'GameScene'
    ) -> str:
        """
        Generate complete Phaser.js code for loading and using the sprite

        Args:
            metadata: Sprite sheet metadata
            texture_key: Texture key
            sprite_sheet_path: Path to sprite sheet
            class_name: Phaser Scene class name

        Returns:
            JavaScript/TypeScript code string
        """
        spritesheet_config = self.generate_spritesheet_config(
            metadata, texture_key, sprite_sheet_path
        )
        animations = self.generate_character_animations(metadata, texture_key)

        code = f"""// Phaser.js Character Setup
// Generated from sprite sheet metadata

class {class_name} extends Phaser.Scene {{
    constructor() {{
        super('{class_name}');
    }}

    preload() {{
        // Load sprite sheet
        this.load.spritesheet(
            '{spritesheet_config['key']}',
            '{spritesheet_config['url']}',
            {{
                frameWidth: {spritesheet_config['frameConfig']['frameWidth']},
                frameHeight: {spritesheet_config['frameConfig']['frameHeight']}
            }}
        );
    }}

    create() {{
        // Create sprite
        this.player = this.add.sprite(400, 300, '{texture_key}');

        // Create animations
"""

        for anim_name, anim_config in animations.items():
            code += f"""        this.anims.create({{
            key: '{anim_config['key']}',
            frames: this.anims.generateFrameNumbers('{texture_key}', {{
                start: {anim_config['frames'][0]['frame']},
                end: {anim_config['frames'][-1]['frame']}
            }}),
            frameRate: {anim_config['frameRate']},
            repeat: {anim_config['repeat']}
        }});

"""

        code += """        // Play initial animation
        this.player.play('idle');

        // Setup keyboard controls
        this.cursors = this.input.keyboard.createCursorKeys();
    }}

    update() {{
        // Handle movement
        if (this.cursors.left.isDown) {{
            this.player.setVelocityX(-160);
            this.player.setFlipX(true);
            this.player.play('walk-left', true);
        }}
        else if (this.cursors.right.isDown) {{
            this.player.setVelocityX(160);
            this.player.setFlipX(false);
            this.player.play('walk-right', true);
        }}
        else {{
            this.player.setVelocityX(0);
            this.player.play('idle', true);
        }}
    }}
}}

// Configuration
const config = {{
    type: Phaser.AUTO,
    width: 800,
    height: 600,
    physics: {{
        default: 'arcade',
        arcade: {{
            gravity: {{ y: 300 }},
            debug: false
        }}
    }},
    scene: {class_name}
}};

const game = new Phaser.Game(config);
"""

        return code

    def save_phaser_config(
        self,
        metadata: dict,
        output_path: Union[str, Path],
        texture_key: str = 'character',
        sprite_sheet_path: str = 'assets/sprites/character.png',
        generate_code: bool = True
    ):
        """
        Save Phaser.js configuration files

        Args:
            metadata: Sprite sheet metadata
            output_path: Output directory or file path
            texture_key: Texture key
            sprite_sheet_path: Sprite sheet path
            generate_code: Whether to generate full Phaser.js code file
        """
        output_path = Path(output_path)

        # Create directory if needed
        if output_path.suffix == '':
            output_path.mkdir(parents=True, exist_ok=True)
            json_path = output_path / f'{texture_key}_config.json'
            code_path = output_path / f'{texture_key}_scene.js'
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            json_path = output_path.with_suffix('.json')
            code_path = output_path.with_suffix('.js')

        # Save JSON configuration
        full_config = {
            'spritesheet': self.generate_spritesheet_config(metadata, texture_key, sprite_sheet_path),
            'animations': self.generate_character_animations(metadata, texture_key)
        }

        with open(json_path, 'w') as f:
            json.dump(full_config, f, indent=2)

        # Generate and save Phaser.js code
        if generate_code:
            code = self.generate_phaser_code(metadata, texture_key, sprite_sheet_path)
            with open(code_path, 'w') as f:
                f.write(code)

        return {
            'config_file': str(json_path),
            'code_file': str(code_path) if generate_code else None
        }
