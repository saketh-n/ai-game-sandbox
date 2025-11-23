"""
Image cache manager for storing and retrieving generated image URLs.
Caches images based on prompt + metadata to avoid regenerating identical images.
"""

import json
import os
from datetime import datetime
from loguru import logger
from typing import Optional, Dict
import hashlib


class ImageCache:
    def __init__(self, cache_file: str = "image_cache.json"):
        self.cache_file = cache_file
        self._ensure_cache_file()

    def _ensure_cache_file(self):
        """Create cache file if it doesn't exist"""
        if not os.path.exists(self.cache_file):
            with open(self.cache_file, 'w') as f:
                json.dump({}, f)
            logger.info(f"Created new image cache file: {self.cache_file}")

    def _generate_cache_key(self, prompt: str, category: str, style: str = "", 
                           additional_instructions: str = "", image_size: str = "", 
                           output_format: str = "") -> str:
        """
        Generate a unique cache key based on all generation parameters.
        Uses MD5 hash of combined parameters for consistent key generation.
        """
        # Combine all parameters that affect image generation
        cache_string = f"{prompt}|{category}|{style}|{additional_instructions}|{image_size}|{output_format}"
        # Generate MD5 hash for a shorter, consistent key
        return hashlib.md5(cache_string.encode()).hexdigest()

    def get(self, prompt: str, category: str, style: str = "", 
            additional_instructions: str = "", image_size: str = "", 
            output_format: str = "") -> Optional[str]:
        """
        Retrieve cached image URL if it exists.
        Returns None if not found.
        """
        try:
            cache_key = self._generate_cache_key(prompt, category, style, 
                                                 additional_instructions, image_size, output_format)
            
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            if cache_key in cache_data:
                entry = cache_data[cache_key]
                logger.info(f"Image cache HIT for key: {cache_key[:16]}... (generated: {entry.get('timestamp')})")
                return entry.get('image_url')
            
            logger.info(f"Image cache MISS for key: {cache_key[:16]}...")
            return None
        
        except Exception as e:
            logger.error(f"Error reading image cache: {str(e)}")
            return None

    def set(self, prompt: str, category: str, image_url: str, style: str = "", 
            additional_instructions: str = "", image_size: str = "", 
            output_format: str = "") -> None:
        """
        Store image URL in cache with metadata.
        """
        try:
            cache_key = self._generate_cache_key(prompt, category, style, 
                                                 additional_instructions, image_size, output_format)
            
            # Read existing cache
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Add new entry
            cache_data[cache_key] = {
                'image_url': image_url,
                'prompt': prompt[:200],  # Store truncated prompt for reference
                'category': category,
                'timestamp': datetime.now().isoformat(),
                'style': style,
                'additional_instructions': additional_instructions[:200],
                'image_size': image_size,
                'output_format': output_format
            }
            
            # Write back to file
            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Image cached with key: {cache_key[:16]}... (URL: {image_url[:50]}...)")
        
        except Exception as e:
            logger.error(f"Error writing to image cache: {str(e)}")

    def get_cache_stats(self) -> Dict:
        """
        Get statistics about the image cache.
        """
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            return {
                'total_images': len(cache_data),
                'cache_file': self.cache_file,
                'cache_size_kb': os.path.getsize(self.cache_file) / 1024
            }
        
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {'total_images': 0, 'error': str(e)}

    def clear(self) -> None:
        """
        Clear all cached images.
        """
        try:
            with open(self.cache_file, 'w') as f:
                json.dump({}, f)
            logger.info("Image cache cleared successfully")
        
        except Exception as e:
            logger.error(f"Error clearing image cache: {str(e)}")
            raise


# Global cache instance
image_cache = ImageCache()

