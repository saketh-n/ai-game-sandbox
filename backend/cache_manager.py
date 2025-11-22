import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

CACHE_FILE = "prompt_cache.json"

class CacheManager:
    def __init__(self, cache_file: str = CACHE_FILE):
        self.cache_file = cache_file
        self.cache_data: Dict = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache from JSON file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading cache: {e}")
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to JSON file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"Error saving cache: {e}")
    
    def get(self, prompt: str) -> Optional[str]:
        """Get cached result for a prompt"""
        return self.cache_data.get(prompt, {}).get('result')
    
    def set(self, prompt: str, result: str):
        """Cache a prompt result"""
        self.cache_data[prompt] = {
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        self._save_cache()
    
    def get_all_prompts(self) -> List[Dict[str, str]]:
        """Get list of all cached prompts with metadata"""
        prompts = []
        for prompt, data in self.cache_data.items():
            prompts.append({
                'prompt': prompt,
                'timestamp': data.get('timestamp', ''),
                'preview': prompt[:100] + '...' if len(prompt) > 100 else prompt
            })
        # Sort by timestamp, newest first
        prompts.sort(key=lambda x: x['timestamp'], reverse=True)
        return prompts
    
    def get_cached_result(self, prompt: str) -> Optional[Dict[str, any]]:
        """Get full cached data for a prompt"""
        if prompt in self.cache_data:
            return {
                'prompt': prompt,
                'result': self.cache_data[prompt]['result'],
                'timestamp': self.cache_data[prompt]['timestamp']
            }
        return None
    
    def exists(self, prompt: str) -> bool:
        """Check if prompt exists in cache"""
        return prompt in self.cache_data
    
    def clear(self):
        """Clear all cache"""
        self.cache_data = {}
        self._save_cache()
    
    def delete(self, prompt: str) -> bool:
        """Delete a specific cached prompt"""
        if prompt in self.cache_data:
            del self.cache_data[prompt]
            self._save_cache()
            return True
        return False

# Global cache instance
cache = CacheManager()

