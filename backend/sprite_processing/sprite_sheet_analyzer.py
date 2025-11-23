"""
Sprite Sheet Layout Analyzer
Uses Claude Vision API to analyze sprite sheet layouts and rearrange them
"""

from PIL import Image
from pathlib import Path
from typing import Tuple, Dict, Any, Optional, Union
import anthropic
import os
import base64
import io
import numpy as np


class SpriteSheetAnalyzer:
    """Analyzes sprite sheet layouts using Claude Vision API"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize analyzer with Anthropic API key"""
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or passed as argument")
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def analyze_sprite_sheet_layout(
        self,
        image_path: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        Analyze sprite sheet layout using Claude Vision API

        Args:
            image_path: Path to sprite sheet image

        Returns:
            Dict with layout information:
            {
                'layout_type': 'horizontal' | 'grid',
                'rows': int,
                'columns': int,
                'total_frames': int,
                'frame_width': int,
                'frame_height': int,
                'explanation': str
            }
        """
        image_path = Path(image_path)

        # Load and encode image
        with open(image_path, 'rb') as f:
            image_data = base64.standard_b64encode(f.read()).decode('utf-8')

        # Determine media type
        ext = image_path.suffix.lower()
        media_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.webp': 'image/webp',
            '.gif': 'image/gif'
        }
        media_type = media_type_map.get(ext, 'image/png')

        # Create vision prompt
        prompt = """Analyze this sprite sheet image for a 2D game character animation.

I need you to determine:
1. **Layout type**: Is it arranged as:
   - 'horizontal': Single row with frames side-by-side (e.g., 1 row × 8 columns)
   - 'grid': Multiple rows and columns (e.g., 2 rows × 4 columns)

2. **Grid dimensions**:
   - Number of rows
   - Number of columns
   - Total number of animation frames

3. **Frame dimensions** (in pixels):
   - Width of each individual frame
   - Height of each individual frame

**Important**:
- Look for repeating character poses/animations
- Each frame should be the same size
- Count actual frames, not empty space
- If there's a grid layout, count how many frames go left-to-right, then top-to-bottom

Please respond in this EXACT JSON format (no markdown, just JSON):
{
    "layout_type": "horizontal or grid",
    "rows": <number>,
    "columns": <number>,
    "total_frames": <number>,
    "frame_width": <pixels>,
    "frame_height": <pixels>,
    "explanation": "Brief description of what you see"
}"""

        # Call Claude Vision API
        message = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }
            ],
        )

        # Parse response
        response_text = message.content[0].text.strip()

        # Try to extract JSON from response
        import json
        try:
            # Remove markdown code blocks if present
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()

            layout_info = json.loads(response_text)

            # Validate required fields
            required_fields = ['layout_type', 'rows', 'columns', 'total_frames', 'frame_width', 'frame_height']
            for field in required_fields:
                if field not in layout_info:
                    raise ValueError(f"Missing required field: {field}")

            return layout_info

        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Failed to parse Claude Vision response: {e}\nResponse: {response_text}")

    def detect_frame_spacing(
        self,
        image_path: Union[str, Path],
        rows: int,
        columns: int,
        frame_width: int,
        frame_height: int
    ) -> Tuple[int, int]:
        """
        Detect horizontal and vertical spacing between frames

        Args:
            image_path: Path to sprite sheet
            rows: Number of rows
            columns: Number of columns
            frame_width: Expected frame width
            frame_height: Expected frame height

        Returns:
            Tuple of (horizontal_spacing, vertical_spacing) in pixels
        """
        sprite_sheet = Image.open(image_path)

        # Calculate what the total size should be without spacing
        expected_width_no_spacing = frame_width * columns
        expected_height_no_spacing = frame_height * rows

        # Calculate spacing based on actual vs expected dimensions
        extra_width = sprite_sheet.width - expected_width_no_spacing
        extra_height = sprite_sheet.height - expected_height_no_spacing

        # Distribute extra space evenly between frames
        h_spacing = extra_width // max(columns - 1, 1) if columns > 1 else 0
        v_spacing = extra_height // max(rows - 1, 1) if rows > 1 else 0

        return (h_spacing, v_spacing)

    def extract_frames_from_grid(
        self,
        image_path: Union[str, Path],
        rows: int,
        columns: int,
        frame_width: int,
        frame_height: int,
        auto_detect_spacing: bool = True
    ) -> list[Image.Image]:
        """
        Extract individual frames from a grid-based sprite sheet

        Args:
            image_path: Path to sprite sheet image
            rows: Number of rows in grid
            columns: Number of columns in grid
            frame_width: Width of each frame in pixels
            frame_height: Height of each frame in pixels
            auto_detect_spacing: Whether to automatically detect spacing between frames

        Returns:
            List of PIL Image objects (frames in left-to-right, top-to-bottom order)
        """
        sprite_sheet = Image.open(image_path)

        if sprite_sheet.mode != 'RGBA':
            sprite_sheet = sprite_sheet.convert('RGBA')

        # Detect spacing if enabled
        h_spacing, v_spacing = 0, 0
        if auto_detect_spacing:
            h_spacing, v_spacing = self.detect_frame_spacing(
                image_path, rows, columns, frame_width, frame_height
            )
            if h_spacing > 0 or v_spacing > 0:
                print(f"  Detected spacing: {h_spacing}px horizontal, {v_spacing}px vertical")

        frames = []

        # Extract frames in reading order (left-to-right, top-to-bottom)
        for row in range(rows):
            for col in range(columns):
                # Calculate position accounting for spacing
                x = col * (frame_width + h_spacing)
                y = row * (frame_height + v_spacing)

                # Crop frame from sprite sheet
                frame = sprite_sheet.crop((
                    x,
                    y,
                    x + frame_width,
                    y + frame_height
                ))

                frames.append(frame)

        return frames

    def extract_frames_smart(
        self,
        image_path: Union[str, Path],
        rows: int,
        columns: int
    ) -> Tuple[list[Image.Image], int, int]:
        """
        Smart frame extraction using gap detection between sprites

        This method:
        1. Finds transparent gaps (vertical columns) between sprites
        2. Uses those gaps as natural split points
        3. Crops each sprite to its actual content bounds
        4. Centers all sprites on consistent-sized canvases

        Args:
            image_path: Path to sprite sheet
            rows: Number of rows in grid
            columns: Number of columns in grid

        Returns:
            Tuple of (frames_list, frame_width, frame_height)
        """
        sprite_sheet = Image.open(image_path)

        if sprite_sheet.mode != 'RGBA':
            sprite_sheet = sprite_sheet.convert('RGBA')

        # For horizontal layouts (1 row), use gap detection
        if rows == 1:
            return self._extract_horizontal_with_gaps(sprite_sheet, columns)

        # For grid layouts, fall back to cell-based extraction
        return self._extract_grid_based(sprite_sheet, rows, columns)

    def _extract_horizontal_with_gaps(
        self,
        sprite_sheet: Image.Image,
        expected_frames: int
    ) -> Tuple[list[Image.Image], int, int]:
        """
        Extract frames using connected component analysis (flood fill)

        This finds cohesive regions of pixels regardless of:
        - Spacing between sprites
        - Gaps within sprites (like between body and tail)
        - Grid alignment

        Args:
            sprite_sheet: PIL Image in RGBA mode
            expected_frames: Expected number of frames

        Returns:
            Tuple of (frames_list, frame_width, frame_height)
        """
        from scipy import ndimage

        alpha = np.array(sprite_sheet)[:, :, 3]

        # Create binary mask (True = has content, False = transparent)
        content_mask = alpha > 10

        # Label connected components
        # structure defines what counts as "connected" (including diagonals)
        structure = np.ones((3, 3), dtype=int)
        labeled_array, num_components = ndimage.label(content_mask, structure=structure)

        print(f"  Found {num_components} connected components")

        # Extract bounding box for each component
        component_boxes = []
        for i in range(1, num_components + 1):
            # Find pixels belonging to this component
            component_mask = labeled_array == i
            rows, cols = np.where(component_mask)

            if len(rows) == 0:
                continue

            # Get bounding box
            min_row, max_row = rows.min(), rows.max()
            min_col, max_col = cols.min(), cols.max()

            # Calculate area (to filter out noise)
            area = (max_row - min_row) * (max_col - min_col)

            component_boxes.append({
                'id': i,
                'left': int(min_col),
                'right': int(max_col + 1),
                'top': int(min_row),
                'bottom': int(max_row + 1),
                'area': area
            })

        # Sort by horizontal position (left to right)
        component_boxes.sort(key=lambda b: b['left'])

        # Filter out very small components (likely noise)
        if len(component_boxes) > 0:
            max_area = max(b['area'] for b in component_boxes)
            min_area_threshold = max_area * 0.01  # Keep components > 1% of largest
            component_boxes = [b for b in component_boxes if b['area'] > min_area_threshold]

        print(f"  After filtering: {len(component_boxes)} sprites detected")

        # If we don't have the expected number, fall back
        if len(component_boxes) != expected_frames:
            print(f"  ⚠️  Connected components found {len(component_boxes)} sprites, expected {expected_frames}")
            print(f"  Falling back to grid-based extraction")
            return self._extract_grid_based(sprite_sheet, 1, expected_frames)

        # Extract each sprite using its bounding box
        frames = []
        max_frame_width = 0
        max_frame_height = 0

        for box in component_boxes:
            # Crop to bounding box
            sprite = sprite_sheet.crop((box['left'], box['top'], box['right'], box['bottom']))

            frames.append(sprite)
            max_frame_width = max(max_frame_width, sprite.width)
            max_frame_height = max(max_frame_height, sprite.height)

        print(f"  Max content size: {max_frame_width}×{max_frame_height}px")

        # Center all frames on consistent canvas
        centered_frames = []
        for frame in frames:
            canvas = Image.new('RGBA', (max_frame_width, max_frame_height), (0, 0, 0, 0))
            x_offset = (max_frame_width - frame.width) // 2
            y_offset = (max_frame_height - frame.height) // 2
            canvas.paste(frame, (x_offset, y_offset), frame)
            centered_frames.append(canvas)

        print(f"  ✓ Extracted {len(centered_frames)} sprites using connected components")
        print(f"  ✓ All frames centered on {max_frame_width}×{max_frame_height}px canvas")

        return centered_frames, max_frame_width, max_frame_height

    def _extract_grid_based(
        self,
        sprite_sheet: Image.Image,
        rows: int,
        columns: int
    ) -> Tuple[list[Image.Image], int, int]:
        """
        Extract frames using equal grid division (fallback method)
        """
        # Calculate cell dimensions (including any spacing)
        cell_width = sprite_sheet.width // columns
        cell_height = sprite_sheet.height // rows

        print(f"  Grid cell size: {cell_width}×{cell_height}px")

        # First pass: extract all cells and find individual content bounds
        all_cells = []
        individual_bounds = []
        max_frame_width = 0
        max_frame_height = 0

        for row in range(rows):
            for col in range(columns):
                # Extract grid cell
                x = col * cell_width
                y = row * cell_height

                cell = sprite_sheet.crop((
                    x,
                    y,
                    x + cell_width,
                    y + cell_height
                ))

                all_cells.append(cell)

                # Find content bounds for THIS specific cell
                if cell.mode == 'RGBA':
                    alpha = np.array(cell)[:, :, 3]
                    rows_with_content = np.where(alpha.max(axis=1) > 10)[0]
                    cols_with_content = np.where(alpha.max(axis=0) > 10)[0]

                    if len(rows_with_content) > 0 and len(cols_with_content) > 0:
                        left = cols_with_content[0]
                        right = cols_with_content[-1] + 1
                        top = rows_with_content[0]
                        bottom = rows_with_content[-1] + 1

                        individual_bounds.append((left, top, right, bottom))

                        # Track max dimensions
                        width = right - left
                        height = bottom - top
                        max_frame_width = max(max_frame_width, width)
                        max_frame_height = max(max_frame_height, height)
                    else:
                        # No content, store full cell bounds
                        individual_bounds.append((0, 0, cell_width, cell_height))
                        max_frame_width = max(max_frame_width, cell_width)
                        max_frame_height = max(max_frame_height, cell_height)
                else:
                    # No alpha channel, use full cell
                    individual_bounds.append((0, 0, cell_width, cell_height))
                    max_frame_width = max(max_frame_width, cell_width)
                    max_frame_height = max(max_frame_height, cell_height)

        print(f"  Max content size across all frames: {max_frame_width}×{max_frame_height}px")

        # Second pass: crop each cell using its own bounds, then center on consistent canvas
        frames = []
        for i, (cell, bounds) in enumerate(zip(all_cells, individual_bounds)):
            left, top, right, bottom = bounds

            # Crop this frame to its own content
            cropped = cell.crop((left, top, right, bottom))

            # Create consistent-sized canvas and center the cropped content
            canvas = Image.new('RGBA', (max_frame_width, max_frame_height), (0, 0, 0, 0))

            # Center the cropped frame on the canvas
            x_offset = (max_frame_width - cropped.width) // 2
            y_offset = (max_frame_height - cropped.height) // 2

            canvas.paste(cropped, (x_offset, y_offset), cropped)
            frames.append(canvas)

        print(f"  ✓ Extracted {len(frames)} frames (expected {rows * columns})")
        print(f"  ✓ All frames centered on {max_frame_width}×{max_frame_height}px canvas")

        return frames, max_frame_width, max_frame_height

    def rearrange_to_horizontal(
        self,
        image_path: Union[str, Path],
        output_path: Union[str, Path],
        layout_info: Optional[Dict[str, Any]] = None
    ) -> Tuple[Path, Dict[str, Any]]:
        """
        Rearrange sprite sheet to horizontal layout (1 row × N columns)

        Args:
            image_path: Path to input sprite sheet
            output_path: Path to save rearranged sprite sheet
            layout_info: Layout info from analyze_sprite_sheet_layout() (if None, will analyze)

        Returns:
            Tuple of (output_path, layout_info)
        """
        image_path = Path(image_path)
        output_path = Path(output_path)

        # Analyze layout if not provided
        if layout_info is None:
            print("🔍 Analyzing sprite sheet layout...")
            layout_info = self.analyze_sprite_sheet_layout(image_path)

        print(f"📊 Layout detected: {layout_info['layout_type']} ({layout_info['rows']}×{layout_info['columns']})")
        print(f"   Frames: {layout_info['total_frames']} @ {layout_info['frame_width']}×{layout_info['frame_height']}px")

        # ALWAYS extract frames using smart content-based extraction
        # This is necessary even for horizontal layouts because:
        # 1. The layout_info dimensions come from Claude Vision's analysis of the ORIGINAL image
        # 2. After background removal, the actual dimensions may be different
        # 3. We need to detect actual content bounds from the CLEANED image
        print("✂️  Extracting frames with content-edge detection...")
        frames, actual_frame_width, actual_frame_height = self.extract_frames_smart(
            image_path,
            rows=layout_info['rows'],
            columns=layout_info['columns']
        )

        # Create horizontal sprite sheet
        print("🔨 Rearranging to horizontal layout...")
        from sprite_processing.sprite_sheet_builder import SpriteSheetBuilder

        builder = SpriteSheetBuilder()
        horizontal_sheet, metadata = builder.create_horizontal_sheet(
            frames=frames,
            frame_width=actual_frame_width,
            frame_height=actual_frame_height,
            spacing=0
        )

        # Save rearranged sprite sheet
        output_path.parent.mkdir(parents=True, exist_ok=True)
        horizontal_sheet.save(output_path, 'PNG')

        print(f"✓ Rearranged sprite sheet saved to: {output_path}")

        # Update layout info with actual detected frame dimensions
        # Convert numpy types to Python types for JSON serialization
        rearranged_info = {
            **layout_info,
            'layout_type': 'horizontal',
            'rows': 1,
            'columns': layout_info['total_frames'],
            'frame_width': int(actual_frame_width),  # Convert from numpy.int64 to Python int
            'frame_height': int(actual_frame_height),  # Convert from numpy.int64 to Python int
            'original_layout': f"{layout_info['rows']}×{layout_info['columns']}",
            'original_frame_width': layout_info['frame_width'],  # Keep Claude's estimate
            'original_frame_height': layout_info['frame_height']  # Keep Claude's estimate
        }

        return output_path, rearranged_info


def main():
    """CLI for testing sprite sheet analyzer"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python sprite_sheet_analyzer.py <sprite_sheet_path> [output_path]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "rearranged_sprite_sheet.png"

    analyzer = SpriteSheetAnalyzer()

    # Analyze and rearrange
    output, info = analyzer.rearrange_to_horizontal(input_path, output_path)

    print("\n✨ Done!")
    print(f"   Output: {output}")
    print(f"   Layout: {info}")


if __name__ == "__main__":
    main()
