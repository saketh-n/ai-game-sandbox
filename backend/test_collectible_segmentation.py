#!/usr/bin/env python3
"""
Test script for collectible sprite segmentation
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from PIL import Image
import numpy as np
from scipy import ndimage
import base64
import io


def segment_collectible_sprites_test(image_path: str):
    """Test the collectible sprite segmentation"""
    print(f"Testing collectible segmentation on: {image_path}")
    
    # Load sprite sheet
    sprite_sheet = Image.open(image_path).convert('RGBA')
    print(f"Image size: {sprite_sheet.width}x{sprite_sheet.height}")
    
    alpha = np.array(sprite_sheet)[:, :, 3]
    
    # Create binary mask
    content_mask = alpha > 10
    
    # Label connected components
    structure = np.ones((3, 3), dtype=int)
    labeled_array, num_components = ndimage.label(content_mask, structure=structure)
    
    print(f"Found {num_components} connected components")
    
    # Extract bounding boxes
    component_boxes = []
    for i in range(1, num_components + 1):
        component_mask = labeled_array == i
        rows, cols = np.where(component_mask)
        
        if len(rows) == 0:
            continue
        
        min_row, max_row = rows.min(), rows.max()
        min_col, max_col = cols.min(), cols.max()
        area = (max_row - min_row) * (max_col - min_col)
        
        component_boxes.append({
            'left': int(min_col),
            'right': int(max_col + 1),
            'top': int(min_row),
            'bottom': int(max_row + 1),
            'area': area,
            'width': int(max_col - min_col + 1),
            'height': int(max_row - min_row + 1)
        })
    
    # Sort by horizontal position
    component_boxes.sort(key=lambda b: b['left'])
    
    # Filter out noise
    if len(component_boxes) > 0:
        max_area = max(b['area'] for b in component_boxes)
        min_area_threshold = max_area * 0.01
        component_boxes = [b for b in component_boxes if b['area'] > min_area_threshold]
    
    print(f"After filtering: {len(component_boxes)} sprites detected")
    
    # Print details
    for i, box in enumerate(component_boxes):
        print(f"  Sprite {i}: pos=({box['left']}, {box['top']}), size=({box['width']}x{box['height']}), area={box['area']}")
    
    return component_boxes


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_collectible_segmentation.py <path_to_collectible_image>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    if not Path(image_path).exists():
        print(f"Error: Image file not found: {image_path}")
        sys.exit(1)
    
    segment_collectible_sprites_test(image_path)

