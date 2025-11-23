"""
Sprite Sheet Builder
Assembles individual frames into sprite sheets for game engines
"""

from PIL import Image
from typing import List, Tuple, Optional, Union
from pathlib import Path
import json


class SpriteSheetBuilder:
    """Assembles individual sprite frames into sprite sheets"""

    def __init__(self):
        """Initialize sprite sheet builder"""
        pass

    def create_horizontal_sheet(
        self,
        frames: List[Image.Image],
        frame_width: Optional[int] = None,
        frame_height: Optional[int] = None,
        spacing: int = 0,
        background_color: Tuple[int, int, int, int] = (0, 0, 0, 0)
    ) -> Tuple[Image.Image, dict]:
        """
        Create a horizontal sprite sheet from individual frames

        Args:
            frames: List of PIL Images (frames)
            frame_width: Fixed width for each frame. If None, uses max width
            frame_height: Fixed height for each frame. If None, uses max height
            spacing: Pixels between frames
            background_color: RGBA background color (default: transparent)

        Returns:
            Tuple of (sprite sheet Image, metadata dict)
        """
        if not frames:
            raise ValueError("No frames provided")

        # Determine frame dimensions
        if frame_width is None:
            frame_width = max(f.width for f in frames)
        if frame_height is None:
            frame_height = max(f.height for f in frames)

        # Calculate total dimensions
        num_frames = len(frames)
        total_width = (frame_width * num_frames) + (spacing * (num_frames - 1))
        total_height = frame_height

        # Create sprite sheet
        sprite_sheet = Image.new('RGBA', (total_width, total_height), background_color)

        # Place frames
        x_offset = 0
        frame_positions = []

        for i, frame in enumerate(frames):
            # Ensure frame is RGBA
            if frame.mode != 'RGBA':
                frame = frame.convert('RGBA')

            # Resize frame if needed
            if frame.size != (frame_width, frame_height):
                # Calculate position to center smaller frames
                temp_frame = Image.new('RGBA', (frame_width, frame_height), (0, 0, 0, 0))
                x_center = (frame_width - frame.width) // 2
                y_center = (frame_height - frame.height) // 2
                temp_frame.paste(frame, (x_center, y_center), frame)
                frame = temp_frame

            # Paste frame onto sprite sheet
            sprite_sheet.paste(frame, (x_offset, 0), frame)

            # Record frame position
            frame_positions.append({
                'frame': i,
                'x': x_offset,
                'y': 0,
                'width': frame_width,
                'height': frame_height
            })

            x_offset += frame_width + spacing

        # Generate metadata
        metadata = {
            'frame_count': num_frames,
            'frame_width': frame_width,
            'frame_height': frame_height,
            'spacing': spacing,
            'sheet_width': total_width,
            'sheet_height': total_height,
            'frames': frame_positions
        }

        return sprite_sheet, metadata

    def create_grid_sheet(
        self,
        frames: List[Image.Image],
        columns: int,
        frame_width: Optional[int] = None,
        frame_height: Optional[int] = None,
        spacing: int = 0,
        background_color: Tuple[int, int, int, int] = (0, 0, 0, 0)
    ) -> Tuple[Image.Image, dict]:
        """
        Create a grid-based sprite sheet from individual frames

        Args:
            frames: List of PIL Images
            columns: Number of columns in grid
            frame_width: Fixed width for each frame
            frame_height: Fixed height for each frame
            spacing: Pixels between frames
            background_color: RGBA background color

        Returns:
            Tuple of (sprite sheet Image, metadata dict)
        """
        if not frames:
            raise ValueError("No frames provided")

        # Determine frame dimensions
        if frame_width is None:
            frame_width = max(f.width for f in frames)
        if frame_height is None:
            frame_height = max(f.height for f in frames)

        # Calculate grid dimensions
        num_frames = len(frames)
        rows = (num_frames + columns - 1) // columns  # Ceiling division

        total_width = (frame_width * columns) + (spacing * (columns - 1))
        total_height = (frame_height * rows) + (spacing * (rows - 1))

        # Create sprite sheet
        sprite_sheet = Image.new('RGBA', (total_width, total_height), background_color)

        # Place frames
        frame_positions = []

        for i, frame in enumerate(frames):
            row = i // columns
            col = i % columns

            x_offset = col * (frame_width + spacing)
            y_offset = row * (frame_height + spacing)

            # Ensure frame is RGBA
            if frame.mode != 'RGBA':
                frame = frame.convert('RGBA')

            # Resize/center frame if needed
            if frame.size != (frame_width, frame_height):
                temp_frame = Image.new('RGBA', (frame_width, frame_height), (0, 0, 0, 0))
                x_center = (frame_width - frame.width) // 2
                y_center = (frame_height - frame.height) // 2
                temp_frame.paste(frame, (x_center, y_center), frame)
                frame = temp_frame

            # Paste frame
            sprite_sheet.paste(frame, (x_offset, y_offset), frame)

            # Record position
            frame_positions.append({
                'frame': i,
                'x': x_offset,
                'y': y_offset,
                'width': frame_width,
                'height': frame_height,
                'row': row,
                'col': col
            })

        # Generate metadata
        metadata = {
            'frame_count': num_frames,
            'columns': columns,
            'rows': rows,
            'frame_width': frame_width,
            'frame_height': frame_height,
            'spacing': spacing,
            'sheet_width': total_width,
            'sheet_height': total_height,
            'frames': frame_positions
        }

        return sprite_sheet, metadata

    def create_animation_sheet(
        self,
        animations: dict[str, List[Image.Image]],
        layout: str = 'horizontal',
        **kwargs
    ) -> Tuple[Image.Image, dict]:
        """
        Create sprite sheet with multiple animations

        Args:
            animations: Dict mapping animation names to frame lists
                       e.g., {'walk': [frame1, frame2], 'run': [frame3, frame4]}
            layout: 'horizontal' or 'grid'
            **kwargs: Additional arguments for create_horizontal_sheet or create_grid_sheet

        Returns:
            Tuple of (sprite sheet Image, metadata dict with animation info)
        """
        # Flatten all frames
        all_frames = []
        animation_metadata = {}
        frame_index = 0

        for anim_name, frames in animations.items():
            num_frames = len(frames)
            all_frames.extend(frames)

            animation_metadata[anim_name] = {
                'start_frame': frame_index,
                'end_frame': frame_index + num_frames - 1,
                'frame_count': num_frames
            }

            frame_index += num_frames

        # Create sprite sheet based on layout
        if layout == 'horizontal':
            sprite_sheet, metadata = self.create_horizontal_sheet(all_frames, **kwargs)
        elif layout == 'grid':
            if 'columns' not in kwargs:
                kwargs['columns'] = 8  # Default columns
            sprite_sheet, metadata = self.create_grid_sheet(all_frames, **kwargs)
        else:
            raise ValueError(f"Unknown layout: {layout}")

        # Add animation info to metadata
        metadata['animations'] = animation_metadata

        return sprite_sheet, metadata

    def save_sprite_sheet(
        self,
        sprite_sheet: Image.Image,
        metadata: dict,
        output_path: Union[str, Path],
        save_metadata: bool = True
    ):
        """
        Save sprite sheet and optionally its metadata

        Args:
            sprite_sheet: PIL Image of sprite sheet
            metadata: Metadata dict
            output_path: Output file path (PNG)
            save_metadata: Whether to save metadata JSON file
        """
        output_path = Path(output_path)

        # Save sprite sheet
        sprite_sheet.save(output_path, 'PNG')

        # Save metadata
        if save_metadata:
            metadata_path = output_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

        return output_path
