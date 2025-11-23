"""
Web Game Exporter
Exports scenes as playable HTML5 games with Phaser.js
"""

from typing import Dict, Union
from pathlib import Path
import base64
import json
import shutil


class WebGameExporter:
    """Exports scenes to playable web games"""

    def __init__(self):
        """Initialize web game exporter"""
        pass

    def export_game(
        self,
        scene_config: Dict,
        output_path: Union[str, Path],
        embed_assets: bool = False  # Changed default to False for better compatibility
    ):
        """
        Export scene as a standalone HTML5 game

        Args:
            scene_config: Scene configuration from SceneGenerator
            output_path: Output HTML file path
            embed_assets: Whether to embed images as base64 (may not work in all browsers)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy assets to output directory
        assets_dir = output_path.parent / "assets"
        assets_dir.mkdir(exist_ok=True)

        # Copy background
        bg_src = Path(scene_config['background']['path'])
        bg_dest = assets_dir / bg_src.name
        if bg_src.resolve() != bg_dest.resolve():
            shutil.copy(bg_src, bg_dest)
        bg_path = f"assets/{bg_src.name}"

        # Copy character sprite
        sprite_src = Path(scene_config['character']['sprite_path'])
        sprite_dest = assets_dir / sprite_src.name
        if sprite_src.resolve() != sprite_dest.resolve():
            shutil.copy(sprite_src, sprite_dest)
        sprite_path = f"assets/{sprite_src.name}"

        # Generate HTML
        html = self._generate_html(scene_config, bg_path, sprite_path)

        # Write to file
        with open(output_path, 'w') as f:
            f.write(html)

        print(f"✓ Playable game exported to: {output_path}")
        print(f"✓ Assets copied to: {assets_dir}")
        print(f"  Open in browser to play!")

    def _generate_html(
        self,
        config: Dict,
        bg_path: str,
        sprite_path: str
    ) -> str:
        """Generate complete HTML5 game"""

        platforms_json = json.dumps(config['physics']['platforms'])

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config['name']} - Playable Game</title>
    <script src="https://cdn.jsdelivr.net/npm/phaser@3.70.0/dist/phaser.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}

        #game-container {{
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 20px;
            margin-bottom: 20px;
        }}

        canvas {{
            border-radius: 8px;
            display: block;
        }}

        .controls {{
            background: rgba(255,255,255,0.95);
            border-radius: 12px;
            padding: 20px 30px;
            max-width: {config['background']['width']}px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        h1 {{
            color: #333;
            margin-bottom: 15px;
            font-size: 1.8rem;
            text-align: center;
        }}

        .controls-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }}

        .control-item {{
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}

        .key {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-family: monospace;
            font-weight: bold;
            margin-right: 8px;
        }}

        .description {{
            color: #666;
            font-size: 0.9rem;
        }}

        .stats {{
            background: rgba(0,0,0,0.7);
            color: white;
            padding: 10px 15px;
            border-radius: 8px;
            margin-top: 15px;
            font-family: monospace;
            font-size: 0.85rem;
        }}

        .footer {{
            color: rgba(255,255,255,0.8);
            margin-top: 20px;
            text-align: center;
            font-size: 0.9rem;
        }}

        .loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            color: white;
            font-size: 1.5rem;
            z-index: 1000;
        }}
    </style>
</head>
<body>
    <div id="loading" class="loading">Loading game...</div>
    <div id="game-container" style="display:none;"></div>

    <div class="controls" id="controls" style="display:none;">
        <h1>🎮 Controls</h1>
        <div class="controls-grid">
            <div class="control-item">
                <span class="key">←</span>
                <span class="key">→</span>
                <div class="description">Move Left/Right</div>
            </div>
            <div class="control-item">
                <span class="key">SPACE</span>
                <div class="description">Jump (Double Jump!)</div>
            </div>
            <div class="control-item">
                <span class="key">R</span>
                <div class="description">Reset Position</div>
            </div>
        </div>
        <div class="stats" id="stats">
            Position: (0, 0) | Velocity: (0, 0) | On Ground: No | Jumps: 0/2
        </div>
    </div>

    <div class="footer" id="footer" style="display:none;">
        Made with Phaser 3 • Press R to reset if character gets stuck
    </div>

    <script>
        class {config['name']} extends Phaser.Scene {{
            constructor() {{
                super('{config['name']}');
            }}

            preload() {{
                // Check if images are data URIs and handle them specially
                const bgPath = '{bg_path}';
                const spritePath = '{sprite_path}';

                if (bgPath.startsWith('data:')) {{
                    // Handle background data URI
                    const bgImage = new Image();
                    bgImage.onload = () => {{
                        this.textures.addImage('background', bgImage);
                        console.log('Background loaded from data URI');
                    }};
                    bgImage.src = bgPath;
                }} else {{
                    this.load.image('background', bgPath);
                }}

                if (spritePath.startsWith('data:')) {{
                    // Handle sprite data URI
                    const spriteImage = new Image();
                    spriteImage.onload = () => {{
                        this.textures.addSpriteSheet('player', spriteImage, {{
                            frameWidth: {config['character']['frame_width']},
                            frameHeight: {config['character']['frame_height']}
                        }});
                        console.log('Sprite sheet loaded from data URI');
                    }};
                    spriteImage.src = spritePath;
                }} else {{
                    this.load.spritesheet('player', spritePath, {{
                        frameWidth: {config['character']['frame_width']},
                        frameHeight: {config['character']['frame_height']}
                    }});
                }}

                // Loading progress
                this.load.on('progress', (value) => {{
                    console.log('Loading: ' + Math.round(value * 100) + '%');
                }});

                this.load.on('complete', () => {{
                    console.log('Assets loaded!');
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('game-container').style.display = 'block';
                    document.getElementById('controls').style.display = 'block';
                    document.getElementById('footer').style.display = 'block';
                }});
            }}

            create() {{
                // Add background
                this.bg = this.add.image(0, 0, 'background').setOrigin(0, 0);

                // Set up physics
                this.physics.world.setBounds(
                    0, 0,
                    {config['physics']['bounds']['width']},
                    {config['physics']['bounds']['height']}
                );

                // Create platforms
                this.platforms = this.physics.add.staticGroup();
                const platformData = {platforms_json};

                platformData.forEach(platform => {{
                    // Create rectangle at top-left position (not center)
                    // Claude Vision returns top-left coordinates, so we set origin to (0, 0)
                    const rect = this.add.rectangle(
                        platform.x,
                        platform.y,
                        platform.width,
                        platform.height,
                        0x00ff00,
                        0.0  // Invisible platforms (set to 0.3 to see them)
                    );
                    // Set origin to top-left to match Claude's coordinate system
                    rect.setOrigin(0, 0);
                    this.physics.add.existing(rect, true);
                    this.platforms.add(rect);
                }});

                // Create player
                this.player = this.physics.add.sprite(
                    {config['character']['spawn_x']},
                    {config['character']['spawn_y']},
                    'player'
                );

                this.player.setBounce(0.1);
                this.player.setCollideWorldBounds(true);
                this.player.setGravityY({config['physics']['gravity']});

                // Scale player to reasonable size
                const targetHeight = 100;  // Target height in pixels
                const scale = targetHeight / {config['character']['frame_height']};
                this.player.setScale(scale);

                // Create animations
                this.anims.create({{
                    key: 'walk',
                    frames: this.anims.generateFrameNumbers('player', {{
                        start: 0,
                        end: {config['character']['num_frames'] - 1}
                    }}),
                    frameRate: 10,
                    repeat: -1
                }});

                this.anims.create({{
                    key: 'idle',
                    frames: [{{ key: 'player', frame: 0 }}],
                    frameRate: 5,
                    repeat: -1
                }});

                // Add one-way platform collider (jump through from below, land on top)
                this.physics.add.collider(this.player, this.platforms, null, (player, platform) => {{
                    // Allow jumping through platforms from below
                    // Only collide if player is falling/standing (velocity.y >= 0)
                    // AND player's bottom is at or above platform's top
                    const playerBottom = player.body.y + player.body.height;
                    const platformTop = platform.body.y;

                    // If player is jumping upward (negative velocity), allow pass-through
                    if (player.body.velocity.y < 0) {{
                        return false;  // No collision - pass through
                    }}

                    // If player's bottom is above the platform top, allow collision
                    // (with small tolerance for smooth landing)
                    if (playerBottom <= platformTop + 10) {{
                        return true;  // Collide - player lands on platform
                    }}

                    // Otherwise no collision (player is inside/below platform)
                    return false;
                }}, this);

                // Set up controls
                this.cursors = this.input.keyboard.createCursorKeys();
                this.spaceKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE);
                this.resetKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.R);

                // Jump tracking
                this.jumpsRemaining = {config['player']['max_jumps']};
                this.isGrounded = false;

                // Camera setup - don't follow if background fits in viewport
                const bgWidth = {config['background']['width']};
                const bgHeight = {config['background']['height']};

                if (bgWidth > config.width || bgHeight > config.height) {{
                    this.cameras.main.setBounds(0, 0, bgWidth, bgHeight);
                    this.cameras.main.startFollow(this.player, true, 0.1, 0.1);
                }}

                // Spawn position
                this.spawnX = {config['character']['spawn_x']};
                this.spawnY = {config['character']['spawn_y']};
            }}

            update() {{
                // Check if on ground
                this.isGrounded = this.player.body.touching.down;

                // Reset jumps when grounded
                if (this.isGrounded) {{
                    this.jumpsRemaining = {config['player']['max_jumps']};
                }}

                // Movement
                if (this.cursors.left.isDown) {{
                    this.player.setVelocityX(-{config['player']['walk_speed']});
                    this.player.setFlipX(true);
                    this.player.play('walk', true);
                }} else if (this.cursors.right.isDown) {{
                    this.player.setVelocityX({config['player']['walk_speed']});
                    this.player.setFlipX(false);
                    this.player.play('walk', true);
                }} else {{
                    this.player.setVelocityX(0);
                    this.player.play('idle', true);
                }}

                // Jumping (double jump support)
                if (Phaser.Input.Keyboard.JustDown(this.spaceKey)) {{
                    if (this.jumpsRemaining > 0) {{
                        this.player.setVelocityY({config['player']['jump_velocity']});
                        this.jumpsRemaining--;
                    }}
                }}

                // Reset position
                if (Phaser.Input.Keyboard.JustDown(this.resetKey)) {{
                    this.player.setPosition(this.spawnX, this.spawnY);
                    this.player.setVelocity(0, 0);
                    this.jumpsRemaining = {config['player']['max_jumps']};
                }}

                // Update stats display
                this.updateStats();
            }}

            updateStats() {{
                const statsDiv = document.getElementById('stats');
                if (statsDiv) {{
                    const x = Math.round(this.player.x);
                    const y = Math.round(this.player.y);
                    const vx = Math.round(this.player.body.velocity.x);
                    const vy = Math.round(this.player.body.velocity.y);
                    const grounded = this.isGrounded ? 'Yes' : 'No';
                    const jumps = ({config['player']['max_jumps']} - this.jumpsRemaining) + '/' + {config['player']['max_jumps']};

                    statsDiv.textContent = `Position: (${{x}}, ${{y}}) | Velocity: (${{vx}}, ${{vy}}) | On Ground: ${{grounded}} | Jumps Used: ${{jumps}}`;
                }}
            }}
        }}

        // Calculate optimal game size to fit screen
        const maxWidth = Math.min(window.innerWidth - 100, {config['background']['width']});
        const maxHeight = Math.min(window.innerHeight - 300, {config['background']['height']});

        // Maintain aspect ratio
        const aspectRatio = {config['background']['width']} / {config['background']['height']};
        let gameWidth = maxWidth;
        let gameHeight = gameWidth / aspectRatio;

        if (gameHeight > maxHeight) {{
            gameHeight = maxHeight;
            gameWidth = gameHeight * aspectRatio;
        }}

        const config = {{
            type: Phaser.AUTO,
            width: Math.round(gameWidth),
            height: Math.round(gameHeight),
            parent: 'game-container',
            physics: {{
                default: 'arcade',
                arcade: {{
                    gravity: {{ y: 0 }},
                    debug: false  // Set to true to see collision boxes
                }}
            }},
            scene: {config['name']},
            pixelArt: true,
            antialias: false,
            scale: {{
                mode: Phaser.Scale.FIT,
                autoCenter: Phaser.Scale.CENTER_BOTH
            }}
        }};

        const game = new Phaser.Game(config);
    </script>
</body>
</html>"""

        return html
