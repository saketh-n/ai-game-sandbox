"""
Game Cache Manager
Caches generated games and intermediate processing results to avoid expensive API calls
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import shutil


class GameCacheManager:
    """Manages caching of generated games and their intermediate data"""
    
    def __init__(self, cache_dir: str = "game_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
    def _generate_cache_key(
        self,
        background_url: str,
        character_url: str,
        mob_url: Optional[str],
        collectible_url: Optional[str],
        num_frames: int
    ) -> str:
        """Generate a unique cache key based on asset URLs and parameters"""
        # Create a deterministic string from all inputs
        cache_string = f"{background_url}|{character_url}|{mob_url or ''}|{collectible_url or ''}|{num_frames}"
        # Hash it to get a clean key
        return hashlib.sha256(cache_string.encode()).hexdigest()[:16]
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get the directory path for a cache key"""
        return self.cache_dir / cache_key
    
    def exists(
        self,
        background_url: str,
        character_url: str,
        mob_url: Optional[str],
        collectible_url: Optional[str],
        num_frames: int
    ) -> bool:
        """Check if a complete game cache exists"""
        cache_key = self._generate_cache_key(
            background_url, character_url, mob_url, collectible_url, num_frames
        )
        cache_path = self._get_cache_path(cache_key)
        
        # Check if game.html exists (indicates complete cache)
        return (cache_path / "game.html").exists()
    
    def get_cached_game(
        self,
        background_url: str,
        character_url: str,
        mob_url: Optional[str],
        collectible_url: Optional[str],
        num_frames: int
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a complete cached game"""
        cache_key = self._generate_cache_key(
            background_url, character_url, mob_url, collectible_url, num_frames
        )
        cache_path = self._get_cache_path(cache_key)
        
        try:
            # Load game HTML
            game_html_path = cache_path / "game.html"
            if not game_html_path.exists():
                return None
            
            with open(game_html_path, 'r', encoding='utf-8') as f:
                game_html = f.read()
            
            # Load scene config
            scene_config_path = cache_path / "scene_config.json"
            with open(scene_config_path, 'r', encoding='utf-8') as f:
                scene_config = json.load(f)
            
            # Load debug frames if they exist
            debug_frames_path = cache_path / "debug_frames.json"
            debug_frames = []
            if debug_frames_path.exists():
                with open(debug_frames_path, 'r', encoding='utf-8') as f:
                    debug_frames = json.load(f)
            
            # Load debug collectibles if they exist
            debug_collectibles_path = cache_path / "debug_collectibles.json"
            debug_collectibles = []
            if debug_collectibles_path.exists():
                with open(debug_collectibles_path, 'r', encoding='utf-8') as f:
                    debug_collectibles = json.load(f)
            
            # Load manifest
            manifest_path = cache_path / "manifest.json"
            manifest = {}
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
            
            return {
                'game_html': game_html,
                'scene_config': scene_config,
                'debug_frames': debug_frames,
                'debug_collectibles': debug_collectibles,
                'cache_key': cache_key,
                'cached_at': manifest.get('cached_at'),
                'metadata': manifest
            }
        
        except Exception as e:
            print(f"Error loading cached game: {e}")
            return None
    
    def save_game(
        self,
        background_url: str,
        character_url: str,
        mob_url: Optional[str],
        collectible_url: Optional[str],
        num_frames: int,
        game_html: str,
        scene_config: Dict[str, Any],
        debug_frames: List[str],
        debug_collectibles: List[Dict[str, Any]],
        platform_analysis: Dict[str, Any] = None,
        collectible_metadata: List[Dict[str, Any]] = None,
        collectible_sprites: List[str] = None
    ):
        """Save a complete game to cache"""
        cache_key = self._generate_cache_key(
            background_url, character_url, mob_url, collectible_url, num_frames
        )
        cache_path = self._get_cache_path(cache_key)
        cache_path.mkdir(exist_ok=True)
        
        try:
            # Save game HTML
            with open(cache_path / "game.html", 'w', encoding='utf-8') as f:
                f.write(game_html)
            
            # Save scene config
            with open(cache_path / "scene_config.json", 'w', encoding='utf-8') as f:
                json.dump(scene_config, f, indent=2)
            
            # Save debug frames
            with open(cache_path / "debug_frames.json", 'w', encoding='utf-8') as f:
                json.dump(debug_frames, f, indent=2)
            
            # Save debug collectibles
            with open(cache_path / "debug_collectibles.json", 'w', encoding='utf-8') as f:
                json.dump(debug_collectibles, f, indent=2)
            
            # Save platform analysis if provided
            if platform_analysis:
                with open(cache_path / "platform_analysis.json", 'w', encoding='utf-8') as f:
                    json.dump(platform_analysis, f, indent=2)
            
            # Save collectible metadata if provided
            if collectible_metadata:
                with open(cache_path / "collectible_metadata.json", 'w', encoding='utf-8') as f:
                    json.dump(collectible_metadata, f, indent=2)
            
            # Save collectible sprites if provided
            if collectible_sprites:
                with open(cache_path / "collectible_sprites.json", 'w', encoding='utf-8') as f:
                    json.dump(collectible_sprites, f, indent=2)
            
            # Save manifest with metadata
            manifest = {
                'cache_key': cache_key,
                'cached_at': datetime.now().isoformat(),
                'background_url': background_url,
                'character_url': character_url,
                'mob_url': mob_url,
                'collectible_url': collectible_url,
                'num_frames': num_frames,
                'platforms_count': len(scene_config.get('physics', {}).get('platforms', [])),
                'has_collectibles': bool(collectible_url),
                'has_mob': bool(mob_url)
            }
            
            with open(cache_path / "manifest.json", 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)
            
            print(f"✓ Game cached successfully: {cache_key}")
            
        except Exception as e:
            print(f"Error saving game to cache: {e}")
            # Clean up partial cache on error
            if cache_path.exists():
                shutil.rmtree(cache_path, ignore_errors=True)
    
    def get_all_cached_games(self) -> List[Dict[str, Any]]:
        """Get list of all cached games with metadata"""
        games = []
        
        for cache_dir in self.cache_dir.iterdir():
            if not cache_dir.is_dir():
                continue
            
            manifest_path = cache_dir / "manifest.json"
            if not manifest_path.exists():
                continue
            
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                games.append(manifest)
            except Exception as e:
                print(f"Error reading manifest for {cache_dir.name}: {e}")
        
        # Sort by cached_at, newest first
        games.sort(key=lambda x: x.get('cached_at', ''), reverse=True)
        return games
    
    def clear_cache(self):
        """Clear all cached games"""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(exist_ok=True)
            print("✓ Game cache cleared")
    
    def delete_cached_game(
        self,
        background_url: str,
        character_url: str,
        mob_url: Optional[str],
        collectible_url: Optional[str],
        num_frames: int
    ) -> bool:
        """Delete a specific cached game"""
        cache_key = self._generate_cache_key(
            background_url, character_url, mob_url, collectible_url, num_frames
        )
        cache_path = self._get_cache_path(cache_key)
        
        if cache_path.exists():
            shutil.rmtree(cache_path)
            print(f"✓ Deleted cached game: {cache_key}")
            return True
        return False
    
    def get_cache_size(self) -> int:
        """Get total size of cache in bytes"""
        total_size = 0
        for cache_dir in self.cache_dir.rglob('*'):
            if cache_dir.is_file():
                total_size += cache_dir.stat().st_size
        return total_size


# Global instance
game_cache = GameCacheManager()

