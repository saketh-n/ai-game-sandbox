"""
Background Remover
Removes solid color backgrounds from character sprites
"""

from PIL import Image
import numpy as np
from typing import Union, Tuple, Optional
from pathlib import Path


class BackgroundRemover:
    """Removes backgrounds from character sprites"""

    def __init__(self, threshold: int = 240):
        """
        Initialize background remover

        Args:
            threshold: Color threshold for white/light background detection (0-255)
                      Pixels with all RGB values >= threshold are considered background
        """
        self.threshold = threshold

    def remove_background(
        self,
        image: Union[str, Path, Image.Image],
        background_color: Optional[Tuple[int, int, int]] = None,
        tolerance: int = 30
    ) -> Image.Image:
        """
        Remove background from an image

        Args:
            image: Input image (path or PIL Image)
            background_color: Specific RGB color to remove. If None, auto-detects white/light backgrounds
            tolerance: Color tolerance for background removal (0-255)

        Returns:
            PIL Image with transparent background (RGBA)
        """
        # Load image
        if isinstance(image, (str, Path)):
            img = Image.open(image)
        else:
            img = image.copy()

        # Convert to RGBA if needed
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # Convert to numpy array
        data = np.array(img)

        # Get RGB channels
        r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]

        if background_color is None:
            # Auto-detect white/light backgrounds
            # Pixels where all RGB values are >= threshold
            mask = (r >= self.threshold) & (g >= self.threshold) & (b >= self.threshold)
        else:
            # Remove specific color with tolerance
            bg_r, bg_g, bg_b = background_color
            mask = (
                (np.abs(r.astype(int) - bg_r) <= tolerance) &
                (np.abs(g.astype(int) - bg_g) <= tolerance) &
                (np.abs(b.astype(int) - bg_b) <= tolerance)
            )

        # Set alpha to 0 for background pixels
        data[mask, 3] = 0

        # Convert back to PIL Image
        result = Image.fromarray(data, 'RGBA')

        return result

    def auto_crop(self, image: Image.Image, padding: int = 0) -> Image.Image:
        """
        Crop image to remove transparent borders

        Args:
            image: Input image with transparency
            padding: Additional padding around cropped content

        Returns:
            Cropped PIL Image
        """
        # Get bounding box of non-transparent pixels
        bbox = image.getbbox()

        if bbox is None:
            # Image is completely transparent
            return image

        # Add padding
        if padding > 0:
            width, height = image.size
            bbox = (
                max(0, bbox[0] - padding),
                max(0, bbox[1] - padding),
                min(width, bbox[2] + padding),
                min(height, bbox[3] + padding)
            )

        return image.crop(bbox)

    def process_sprite(
        self,
        image: Union[str, Path, Image.Image],
        output_size: Optional[Tuple[int, int]] = None,
        auto_crop_enabled: bool = True,
        crop_padding: int = 5
    ) -> Image.Image:
        """
        Complete sprite processing: remove background, crop, and optionally resize

        Args:
            image: Input image
            output_size: Target size (width, height). If None, keeps original size
            auto_crop_enabled: Whether to auto-crop transparent borders
            crop_padding: Padding around cropped content

        Returns:
            Processed PIL Image with transparent background
        """
        # Remove background
        processed = self.remove_background(image)

        # Auto-crop if enabled
        if auto_crop_enabled:
            processed = self.auto_crop(processed, padding=crop_padding)

        # Resize if requested
        if output_size is not None:
            processed = processed.resize(output_size, Image.Resampling.LANCZOS)

        return processed

    def batch_process(
        self,
        images: list[Union[str, Path, Image.Image]],
        output_size: Optional[Tuple[int, int]] = None,
        auto_crop_enabled: bool = True
    ) -> list[Image.Image]:
        """
        Process multiple sprites

        Args:
            images: List of input images
            output_size: Target size for all sprites
            auto_crop_enabled: Whether to auto-crop

        Returns:
            List of processed PIL Images
        """
        return [
            self.process_sprite(img, output_size, auto_crop_enabled)
            for img in images
        ]
