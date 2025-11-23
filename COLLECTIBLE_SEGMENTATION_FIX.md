# Collectible Segmentation Fix

## Problem
The initial implementation of collectible sprite segmentation was doing raw connected component analysis directly in `main.py`, which was inconsistent with how character sprites are processed. This meant collectibles were not being properly:
1. Analyzed with Claude Vision for layout detection
2. Background-removed before segmentation
3. Extracted using the smart frame detection algorithm
4. Centered and normalized on consistent canvases

## Solution
Updated `segment_collectible_sprites()` to use the **exact same pipeline** as character sprite processing, ensuring consistency and proper segmentation.

## Changes Made

### 1. Updated `backend/main.py`

#### Added Import
```python
from sprite_processing.sprite_sheet_analyzer import SpriteSheetAnalyzer
```

#### Rewrote `segment_collectible_sprites()` Function
**Before:** Raw connected component analysis
**After:** Full sprite sheet processing pipeline

The new function now:
1. **Analyzes layout with Claude Vision API**
   - Detects if sprite sheet is horizontal, grid, or scattered
   - Determines number of rows, columns, and total frames
   - Gets estimated frame dimensions

2. **Removes background**
   - Uses `BackgroundRemover` (same as character sprites)
   - Assumes white background with tolerance=40
   - Auto-crops to remove excess transparent space

3. **Extracts frames using smart extraction**
   - Uses `extract_frames_smart()` method
   - For horizontal layouts: connected component analysis (`_extract_horizontal_with_gaps`)
   - For grid layouts: cell-based extraction with gap detection
   - Finds actual content bounds after background removal

4. **Converts to base64 data URLs**
   - Each extracted frame is converted to PNG
   - Encoded as base64 data URL for embedding in game HTML

#### Updated Function Call
Moved `GameGenerator` initialization **before** collectible processing so we can access `game_gen.sprite_analyzer`:

```python
# Initialize game generator (need it for sprite_analyzer)
output_dir = temp_path / "generated_game"
game_gen = GameGenerator(output_dir=str(output_dir))

# Segment collectible sprites using the same analyzer
collectible_sprites = await asyncio.to_thread(
    segment_collectible_sprites,
    coll_path,
    game_gen.sprite_analyzer  # Pass the sprite analyzer
)
```

## Processing Pipeline Comparison

### Character Sprites (Existing)
```
1. Download character sprite sheet
2. Analyze layout with Claude Vision (SpriteSheetAnalyzer)
3. Remove background (BackgroundRemover)
4. Extract frames (extract_frames_smart → _extract_horizontal_with_gaps)
5. Rebuild as horizontal strip (SpriteSheetBuilder)
6. Convert to base64 for embedding
```

### Collectible Sprites (Now Fixed)
```
1. Download collectible sprite sheet
2. Analyze layout with Claude Vision (SpriteSheetAnalyzer) ✅ NEW
3. Remove background (BackgroundRemover) ✅ NEW
4. Extract frames (extract_frames_smart → _extract_horizontal_with_gaps) ✅ FIXED
5. Convert each frame to base64 data URL
6. Pass array of individual sprites to game
```

## Key Algorithm: Connected Component Analysis

Both character and collectible sprites now use the same extraction method from `SpriteSheetAnalyzer._extract_horizontal_with_gaps()`:

```python
def _extract_horizontal_with_gaps(sprite_sheet, expected_frames):
    # 1. Extract alpha channel
    alpha = np.array(sprite_sheet)[:, :, 3]
    
    # 2. Create binary mask
    content_mask = alpha > 10
    
    # 3. Label connected components (8-connectivity)
    structure = np.ones((3, 3), dtype=int)
    labeled_array, num_components = ndimage.label(content_mask, structure=structure)
    
    # 4. Extract bounding box for each component
    for i in range(1, num_components + 1):
        component_mask = labeled_array == i
        rows, cols = np.where(component_mask)
        min_row, max_row = rows.min(), rows.max()
        min_col, max_col = cols.min(), cols.max()
        # Crop sprite using bounding box
        sprite = sprite_sheet.crop((min_col, min_row, max_col+1, max_row+1))
    
    # 5. Filter noise (< 1% of largest sprite area)
    # 6. Sort left-to-right
    # 7. Center all frames on consistent canvas size
```

This method:
- ✅ Works with any layout (grid, horizontal, scattered)
- ✅ Handles sprites with internal gaps (donuts, rings)
- ✅ Automatically filters noise
- ✅ Sorts sprites consistently
- ✅ Centers sprites for uniform appearance

## Why This Matters

### Before (Raw Connected Components)
- ❌ No layout analysis → guessing frame count
- ❌ No background removal → white pixels treated as sprite content
- ❌ No frame centering → inconsistent sprite sizes
- ❌ Manual bounding box extraction → error-prone
- ❌ Different logic than character sprites → inconsistent results

### After (Full Pipeline)
- ✅ Claude Vision detects exact layout
- ✅ Background removed before extraction
- ✅ Frames centered on consistent canvas
- ✅ Uses battle-tested extraction logic
- ✅ Same pipeline as character sprites → predictable results

## Example Workflow

### Input: Collectible Sprite Sheet
```
┌──────────────────────────────────────┐
│  ⭐    💎    🪙    🔑    ❤️           │  (on white background)
└──────────────────────────────────────┘
```

### Step 1: Claude Vision Analysis
```
{
  "layout_type": "horizontal",
  "rows": 1,
  "columns": 5,
  "total_frames": 5,
  "frame_width": 64,
  "frame_height": 64
}
```

### Step 2: Background Removal
```
┌──────────────────────────────────────┐
│  ⭐    💎    🪙    🔑    ❤️           │  (transparent background)
└──────────────────────────────────────┘
```

### Step 3: Connected Component Extraction
```
Component 1: ⭐ (bounding box: x=10, y=5, w=50, h=52)
Component 2: 💎 (bounding box: x=80, y=8, w=48, h=55)
Component 3: 🪙 (bounding box: x=150, y=10, w=45, h=45)
Component 4: 🔑 (bounding box: x=220, y=7, w=52, h=58)
Component 5: ❤️ (bounding box: x=290, y=12, w=46, h=42)
```

### Step 4: Individual Sprites (Base64 Data URLs)
```javascript
[
  "data:image/png;base64,iVBORw0KGgoAAAANS...", // ⭐
  "data:image/png;base64,iVBORw0KGgoAAAANS...", // 💎
  "data:image/png;base64,iVBORw0KGgoAAAANS...", // 🪙
  "data:image/png;base64,iVBORw0KGgoAAAANS...", // 🔑
  "data:image/png;base64,iVBORw0KGgoAAAANS..."  // ❤️
]
```

### Step 5: Game Uses Individual Sprites
```javascript
// In Phaser preload()
collectibleSprites.forEach((dataUrl, i) => {
  this.textures.addImage('collectible_' + i, dataUrl);
});

// In Phaser create()
collectiblePositions.forEach(pos => {
  const sprite = this.physics.add.sprite(
    pos.x, pos.y,
    'collectible_' + pos.sprite_index  // Random sprite from 0-4
  );
});
```

## Testing

To verify segmentation works correctly:

```bash
cd backend
python test_collectible_segmentation.py path/to/collectible_sheet.png
```

This will:
- Analyze the layout
- Segment the sprites
- Print details for each detected sprite
- Show frame count and dimensions

## Files Modified

1. **`backend/main.py`**
   - Added import for `SpriteSheetAnalyzer`
   - Rewrote `segment_collectible_sprites()` to use full pipeline
   - Moved `GameGenerator` initialization before collectible processing
   - Updated function call to pass `sprite_analyzer`

2. **No changes needed to:**
   - `backend/scene_builder/web_exporter.py` - already handles sprite array correctly
   - `backend/game_generator.py` - already has sprite_analyzer
   - Frontend files - already pass collectible URL correctly

## Benefits

1. **Consistency**: Collectibles and characters use identical processing
2. **Reliability**: Battle-tested extraction algorithm
3. **Flexibility**: Handles any sprite sheet layout (grid, horizontal, scattered)
4. **Quality**: Background removal and centering for clean sprites
5. **Intelligence**: Claude Vision detects layout automatically
6. **Maintainability**: Reuses existing code instead of duplicating logic

## Summary

The collectible segmentation now uses the **exact same pipeline** as character sprite processing, ensuring consistent, high-quality results. The key improvement is using `SpriteSheetAnalyzer` with Claude Vision analysis and background removal, rather than raw connected component analysis.

