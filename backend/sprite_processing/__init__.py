"""
Sprite Processing Module
Handles background removal, sprite sheet assembly, layout analysis, and Phaser.js configuration generation
"""

from .background_remover import BackgroundRemover
from .sprite_sheet_builder import SpriteSheetBuilder
from .sprite_sheet_analyzer import SpriteSheetAnalyzer
from .phaser_config import PhaserConfigGenerator

__all__ = [
    'BackgroundRemover',
    'SpriteSheetBuilder',
    'SpriteSheetAnalyzer',
    'PhaserConfigGenerator',
]
