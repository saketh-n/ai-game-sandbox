"""
Sprite Processing Module
Handles background removal, sprite sheet assembly, and Phaser.js configuration generation
"""

from .background_remover import BackgroundRemover
from .sprite_sheet_builder import SpriteSheetBuilder
from .phaser_config import PhaserConfigGenerator

__all__ = [
    'BackgroundRemover',
    'SpriteSheetBuilder',
    'PhaserConfigGenerator',
]
