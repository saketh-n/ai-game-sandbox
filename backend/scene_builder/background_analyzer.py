"""
Background Analyzer
Analyzes background images to detect walkable paths and collision areas
"""

from PIL import Image
import numpy as np
from typing import Tuple, List, Dict, Union, Optional
from pathlib import Path


class BackgroundAnalyzer:
    """Analyzes backgrounds to find walkable paths"""

    def __init__(self):
        """Initialize background analyzer"""
        pass

    def analyze_ground_level(
        self,
        background: Union[str, Path, Image.Image],
        sample_width: int = 10
    ) -> Dict:
        """
        Analyze background to find ground level for walking

        Args:
            background: Background image
            sample_width: Width in pixels to sample for ground detection

        Returns:
            Dict with ground level data and walkable regions
        """
        # Load image
        if isinstance(background, (str, Path)):
            img = Image.open(background)
        else:
            img = background.copy()

        # Convert to RGBA
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        width, height = img.size
        data = np.array(img)

        # Detect ground level by scanning from bottom up
        ground_heights = []
        num_samples = width // sample_width

        for i in range(num_samples):
            x = i * sample_width + sample_width // 2

            # Scan from bottom up to find first non-transparent pixel
            ground_y = height - 1  # Default to bottom

            for y in range(height - 1, -1, -1):
                pixel = data[y, x]
                # Check if pixel is not transparent and not pure white/background
                if pixel[3] > 128:  # Not transparent
                    if not (pixel[0] > 240 and pixel[1] > 240 and pixel[2] > 240):  # Not white
                        ground_y = y
                        break

            ground_heights.append({
                'x': x,
                'y': ground_y
            })

        # Calculate average ground level
        avg_ground = sum(p['y'] for p in ground_heights) / len(ground_heights)

        # Find walkable regions (flat-ish areas)
        walkable_regions = self._find_walkable_regions(ground_heights, tolerance=20)

        return {
            'width': width,
            'height': height,
            'ground_points': ground_heights,
            'average_ground': avg_ground,
            'walkable_regions': walkable_regions,
            'sample_width': sample_width
        }

    def _find_walkable_regions(
        self,
        ground_points: List[Dict],
        tolerance: int = 20
    ) -> List[Dict]:
        """
        Find flat walkable regions from ground points

        Args:
            ground_points: List of ground height points
            tolerance: Height variation tolerance for walkable area

        Returns:
            List of walkable region dicts
        """
        if not ground_points:
            return []

        regions = []
        current_region = {
            'start_x': ground_points[0]['x'],
            'end_x': ground_points[0]['x'],
            'min_y': ground_points[0]['y'],
            'max_y': ground_points[0]['y']
        }

        for i in range(1, len(ground_points)):
            point = ground_points[i]
            prev_point = ground_points[i - 1]

            height_diff = abs(point['y'] - prev_point['y'])

            if height_diff <= tolerance:
                # Continue current region
                current_region['end_x'] = point['x']
                current_region['min_y'] = min(current_region['min_y'], point['y'])
                current_region['max_y'] = max(current_region['max_y'], point['y'])
            else:
                # Start new region
                if current_region['end_x'] - current_region['start_x'] > 50:  # Min width
                    regions.append(current_region)

                current_region = {
                    'start_x': point['x'],
                    'end_x': point['x'],
                    'min_y': point['y'],
                    'max_y': point['y']
                }

        # Add final region
        if current_region['end_x'] - current_region['start_x'] > 50:
            regions.append(current_region)

        return regions

    def create_ground_platform(
        self,
        analysis: Dict,
        platform_thickness: int = 50
    ) -> List[Dict]:
        """
        Create platform collision boxes from ground analysis

        Args:
            analysis: Ground analysis data
            platform_thickness: Thickness of platform collision box

        Returns:
            List of platform dicts with x, y, width, height
        """
        platforms = []

        for region in analysis['walkable_regions']:
            platform = {
                'x': region['start_x'],
                'y': region['max_y'],  # Top of walkable area
                'width': region['end_x'] - region['start_x'],
                'height': platform_thickness
            }
            platforms.append(platform)

        # If no walkable regions found, create a simple ground platform
        if not platforms:
            platforms.append({
                'x': 0,
                'y': analysis['average_ground'],
                'width': analysis['width'],
                'height': platform_thickness
            })

        return platforms

    def visualize_analysis(
        self,
        background: Union[str, Path, Image.Image],
        analysis: Dict,
        output_path: Optional[str] = None
    ) -> Image.Image:
        """
        Create visualization of ground analysis

        Args:
            background: Original background image
            analysis: Analysis data
            output_path: Optional path to save visualization

        Returns:
            PIL Image with visualization overlay
        """
        # Load background
        if isinstance(background, (str, Path)):
            img = Image.open(background).convert('RGBA')
        else:
            img = background.copy().convert('RGBA')

        # Create overlay
        from PIL import ImageDraw
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Draw ground points
        for point in analysis['ground_points']:
            x, y = point['x'], point['y']
            draw.ellipse([x-3, y-3, x+3, y+3], fill=(255, 0, 0, 200))

        # Draw walkable regions
        for region in analysis['walkable_regions']:
            draw.rectangle([
                region['start_x'],
                region['min_y'],
                region['end_x'],
                region['max_y']
            ], outline=(0, 255, 0, 200), width=2)

        # Draw average ground line
        draw.line([
            (0, analysis['average_ground']),
            (analysis['width'], analysis['average_ground'])
        ], fill=(0, 0, 255, 150), width=2)

        # Composite
        result = Image.alpha_composite(img, overlay)

        if output_path:
            result.save(output_path)

        return result
