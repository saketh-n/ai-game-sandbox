"""
Component Cache Manager
Implements granular component-level caching for game generation
Each component (background, character, mob, collectible) is cached independently
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import shutil
import base64


class ComponentCacheManager:
    """Manages caching of individual game components"""
    
    def __init__(self, cache_dir: str = "game_cache/components"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def _generate_component_key(self, component_type: str, url: str, **kwargs) -> str:
        """
        Generate a unique cache key for a component
        
        Args:
            component_type: 'background', 'character', 'mob', or 'collectible'
            url: The asset URL
            **kwargs: Additional parameters that affect processing (e.g., num_frames)
        """
        # Include all parameters that affect the output
        cache_string = f"{component_type}|{url}"
        for key in sorted(kwargs.keys()):
            cache_string += f"|{key}={kwargs[key]}"
        
        # Hash to get clean key
        hash_val = hashlib.sha256(cache_string.encode()).hexdigest()[:16]
        return f"{component_type}_{hash_val}"
    
    def _get_component_path(self, component_key: str) -> Path:
        """Get the directory path for a component"""
        return self.cache_dir / component_key
    
    # ============ BACKGROUND COMPONENT ============
    
    def get_background_component(self, background_url: str) -> Optional[Dict[str, Any]]:
        """Get cached background platform analysis"""
        component_key = self._generate_component_key("background", background_url)
        component_path = self._get_component_path(component_key)
        
        platform_analysis_path = component_path / "platform_analysis.json"
        if not platform_analysis_path.exists():
            return None
        
        try:
            with open(platform_analysis_path, 'r', encoding='utf-8') as f:
                platform_analysis = json.load(f)
            
            metadata_path = component_path / "metadata.json"
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            return {
                'platform_analysis': platform_analysis,
                'component_key': component_key,
                'metadata': metadata
            }
        except Exception as e:
            print(f"Error loading background component: {e}")
            return None
    
    def save_background_component(
        self,
        background_url: str,
        platform_analysis: Dict[str, Any]
    ) -> str:
        """Save background platform analysis to cache"""
        component_key = self._generate_component_key("background", background_url)
        component_path = self._get_component_path(component_key)
        component_path.mkdir(exist_ok=True)
        
        try:
            # Save platform analysis
            with open(component_path / "platform_analysis.json", 'w', encoding='utf-8') as f:
                json.dump(platform_analysis, f, indent=2)
            
            # Save metadata
            metadata = {
                'component_type': 'background',
                'component_key': component_key,
                'url': background_url,
                'cached_at': datetime.now().isoformat(),
                'platforms_count': len(platform_analysis.get('platforms', []))
            }
            with open(component_path / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✓ Cached background component: {component_key}")
            return component_key
        except Exception as e:
            print(f"Error saving background component: {e}")
            if component_path.exists():
                shutil.rmtree(component_path, ignore_errors=True)
            raise
    
    # ============ CHARACTER COMPONENT ============
    
    def get_character_component(self, character_url: str, num_frames: int) -> Optional[Dict[str, Any]]:
        """Get cached character sprite processing results"""
        component_key = self._generate_component_key("character", character_url, num_frames=num_frames)
        component_path = self._get_component_path(component_key)
        
        sprite_config_path = component_path / "sprite_config.json"
        processed_sprite_path = component_path / "processed_sprite_base64.txt"
        
        if not (sprite_config_path.exists() and processed_sprite_path.exists()):
            return None
        
        try:
            # Load sprite config
            with open(sprite_config_path, 'r', encoding='utf-8') as f:
                sprite_config = json.load(f)
            
            # Load processed sprite
            with open(processed_sprite_path, 'r', encoding='utf-8') as f:
                processed_sprite_data_url = f.read()
            
            # Load debug frames if they exist
            debug_frames_path = component_path / "debug_frames.json"
            debug_frames = []
            if debug_frames_path.exists():
                with open(debug_frames_path, 'r', encoding='utf-8') as f:
                    debug_frames = json.load(f)
            
            # Load metadata
            metadata_path = component_path / "metadata.json"
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            return {
                'sprite_config': sprite_config,
                'processed_sprite_data_url': processed_sprite_data_url,
                'debug_frames': debug_frames,
                'component_key': component_key,
                'metadata': metadata
            }
        except Exception as e:
            print(f"Error loading character component: {e}")
            return None
    
    def save_character_component(
        self,
        character_url: str,
        num_frames: int,
        sprite_config: Dict[str, Any],
        processed_sprite_data_url: str,
        debug_frames: list = None
    ) -> str:
        """Save character sprite processing results to cache"""
        component_key = self._generate_component_key("character", character_url, num_frames=num_frames)
        component_path = self._get_component_path(component_key)
        component_path.mkdir(exist_ok=True)
        
        try:
            # Save sprite config
            with open(component_path / "sprite_config.json", 'w', encoding='utf-8') as f:
                json.dump(sprite_config, f, indent=2)
            
            # Save processed sprite data URL
            with open(component_path / "processed_sprite_base64.txt", 'w', encoding='utf-8') as f:
                f.write(processed_sprite_data_url)
            
            # Save debug frames if provided
            if debug_frames:
                with open(component_path / "debug_frames.json", 'w', encoding='utf-8') as f:
                    json.dump(debug_frames, f, indent=2)
            
            # Save metadata
            metadata = {
                'component_type': 'character',
                'component_key': component_key,
                'url': character_url,
                'num_frames': num_frames,
                'cached_at': datetime.now().isoformat(),
                'frame_width': sprite_config.get('frame_width'),
                'frame_height': sprite_config.get('frame_height')
            }
            with open(component_path / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✓ Cached character component: {component_key}")
            return component_key
        except Exception as e:
            print(f"Error saving character component: {e}")
            if component_path.exists():
                shutil.rmtree(component_path, ignore_errors=True)
            raise
    
    # ============ MOB COMPONENT ============
    
    def get_mob_component(self, mob_url: str, num_frames: int) -> Optional[Dict[str, Any]]:
        """Get cached mob sprite processing results"""
        component_key = self._generate_component_key("mob", mob_url, num_frames=num_frames)
        component_path = self._get_component_path(component_key)
        
        sprite_config_path = component_path / "sprite_config.json"
        processed_sprite_path = component_path / "processed_sprite_base64.txt"
        
        if not (sprite_config_path.exists() and processed_sprite_path.exists()):
            return None
        
        try:
            # Load sprite config
            with open(sprite_config_path, 'r', encoding='utf-8') as f:
                sprite_config = json.load(f)
            
            # Load processed sprite
            with open(processed_sprite_path, 'r', encoding='utf-8') as f:
                processed_sprite_data_url = f.read()
            
            # Load metadata
            metadata_path = component_path / "metadata.json"
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            return {
                'sprite_config': sprite_config,
                'processed_sprite_data_url': processed_sprite_data_url,
                'component_key': component_key,
                'metadata': metadata
            }
        except Exception as e:
            print(f"Error loading mob component: {e}")
            return None
    
    def save_mob_component(
        self,
        mob_url: str,
        num_frames: int,
        sprite_config: Dict[str, Any],
        processed_sprite_data_url: str
    ) -> str:
        """Save mob sprite processing results to cache"""
        component_key = self._generate_component_key("mob", mob_url, num_frames=num_frames)
        component_path = self._get_component_path(component_key)
        component_path.mkdir(exist_ok=True)
        
        try:
            # Save sprite config
            with open(component_path / "sprite_config.json", 'w', encoding='utf-8') as f:
                json.dump(sprite_config, f, indent=2)
            
            # Save processed sprite data URL
            with open(component_path / "processed_sprite_base64.txt", 'w', encoding='utf-8') as f:
                f.write(processed_sprite_data_url)
            
            # Save metadata
            metadata = {
                'component_type': 'mob',
                'component_key': component_key,
                'url': mob_url,
                'num_frames': num_frames,
                'cached_at': datetime.now().isoformat(),
                'frame_width': sprite_config.get('frame_width'),
                'frame_height': sprite_config.get('frame_height')
            }
            with open(component_path / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✓ Cached mob component: {component_key}")
            return component_key
        except Exception as e:
            print(f"Error saving mob component: {e}")
            if component_path.exists():
                shutil.rmtree(component_path, ignore_errors=True)
            raise
    
    # ============ COLLECTIBLE COMPONENT ============
    
    def get_collectible_component(self, collectible_url: str) -> Optional[Dict[str, Any]]:
        """Get cached collectible analysis and sprites"""
        component_key = self._generate_component_key("collectible", collectible_url)
        component_path = self._get_component_path(component_key)
        
        metadata_analysis_path = component_path / "collectible_metadata.json"
        sprites_path = component_path / "collectible_sprites.json"
        
        if not (metadata_analysis_path.exists() and sprites_path.exists()):
            return None
        
        try:
            # Load collectible metadata (from Claude Vision)
            with open(metadata_analysis_path, 'r', encoding='utf-8') as f:
                collectible_metadata = json.load(f)
            
            # Load segmented sprites
            with open(sprites_path, 'r', encoding='utf-8') as f:
                collectible_sprites = json.load(f)
            
            # Load metadata
            metadata_path = component_path / "metadata.json"
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            
            return {
                'collectible_metadata': collectible_metadata,
                'collectible_sprites': collectible_sprites,
                'component_key': component_key,
                'metadata': metadata
            }
        except Exception as e:
            print(f"Error loading collectible component: {e}")
            return None
    
    def save_collectible_component(
        self,
        collectible_url: str,
        collectible_metadata: list,
        collectible_sprites: list
    ) -> str:
        """Save collectible analysis and sprites to cache"""
        component_key = self._generate_component_key("collectible", collectible_url)
        component_path = self._get_component_path(component_key)
        component_path.mkdir(exist_ok=True)
        
        try:
            # Save collectible metadata
            with open(component_path / "collectible_metadata.json", 'w', encoding='utf-8') as f:
                json.dump(collectible_metadata, f, indent=2)
            
            # Save collectible sprites
            with open(component_path / "collectible_sprites.json", 'w', encoding='utf-8') as f:
                json.dump(collectible_sprites, f, indent=2)
            
            # Save metadata
            metadata = {
                'component_type': 'collectible',
                'component_key': component_key,
                'url': collectible_url,
                'cached_at': datetime.now().isoformat(),
                'collectibles_count': len(collectible_metadata),
                'sprites_count': len(collectible_sprites)
            }
            with open(component_path / "metadata.json", 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"✓ Cached collectible component: {component_key}")
            return component_key
        except Exception as e:
            print(f"Error saving collectible component: {e}")
            if component_path.exists():
                shutil.rmtree(component_path, ignore_errors=True)
            raise
    
    # ============ UTILITY METHODS ============
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about cached components"""
        stats = {
            'background': 0,
            'character': 0,
            'mob': 0,
            'collectible': 0,
            'total_size_bytes': 0
        }
        
        if not self.cache_dir.exists():
            return stats
        
        for component_dir in self.cache_dir.iterdir():
            if not component_dir.is_dir():
                continue
            
            # Count by type
            component_name = component_dir.name
            if component_name.startswith('background_'):
                stats['background'] += 1
            elif component_name.startswith('character_'):
                stats['character'] += 1
            elif component_name.startswith('mob_'):
                stats['mob'] += 1
            elif component_name.startswith('collectible_'):
                stats['collectible'] += 1
            
            # Calculate size
            for file_path in component_dir.rglob('*'):
                if file_path.is_file():
                    stats['total_size_bytes'] += file_path.stat().st_size
        
        stats['total_components'] = sum([
            stats['background'],
            stats['character'],
            stats['mob'],
            stats['collectible']
        ])
        stats['total_size_mb'] = round(stats['total_size_bytes'] / (1024 * 1024), 2)
        
        return stats
    
    def clear_cache(self):
        """Clear all cached components"""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            print("✓ Component cache cleared")


# Global instance
component_cache = ComponentCacheManager()

