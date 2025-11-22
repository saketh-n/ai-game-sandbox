"""
Configuration for image generation
"""

from dataclasses import dataclass, field
from typing import Optional, List, Union
from pathlib import Path
from PIL import Image


@dataclass
class ImageGenerationConfig:
    """Configuration for image generation using FAL AI"""

    model_name: str
    prompt: str
    inspiration_images: List[Union[str, Path, Image.Image, bytes]] = field(default_factory=list)
    cfg_scale: float = 7.5
    num_inference_steps: int = 25
    width: int = 1024
    height: int = 1024
    num_images: int = 1
    seed: Optional[int] = None

    def __post_init__(self):
        """Validate configuration parameters"""
        if self.cfg_scale < 0 or self.cfg_scale > 20:
            raise ValueError("cfg_scale must be between 0 and 20")

        if self.num_inference_steps < 1 or self.num_inference_steps > 150:
            raise ValueError("num_inference_steps must be between 1 and 150")

        if self.width < 64 or self.height < 64:
            raise ValueError("width and height must be at least 64")

        if self.num_images < 1:
            raise ValueError("num_images must be at least 1")

    def to_dict(self) -> dict:
        """Convert config to dictionary for API calls"""
        from .utils import process_inspiration_image

        config_dict = {
            'prompt': self.prompt,
            'guidance_scale': self.cfg_scale,
            'num_inference_steps': self.num_inference_steps,
            'image_size': {
                'width': self.width,
                'height': self.height
            },
            'num_images': self.num_images,
        }

        if self.seed is not None:
            config_dict['seed'] = self.seed

        if self.inspiration_images:
            # Process all inspiration images (convert local files/PIL Images to data URIs)
            processed_images = [
                process_inspiration_image(img) for img in self.inspiration_images
            ]
            config_dict['image_url'] = processed_images[0]
            if len(processed_images) > 1:
                config_dict['reference_images'] = processed_images[1:]

        return config_dict
