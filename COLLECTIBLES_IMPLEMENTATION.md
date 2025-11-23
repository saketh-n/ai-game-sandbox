# Collectibles Implementation

## Overview
Implemented collectible item spawning with collision detection in the generated platformer games. Collectibles are automatically placed on platforms using connected component analysis for sprite segmentation.

## Key Features

### 1. Sprite Segmentation
- Uses **connected component analysis** (flood-fill style segmentation) to extract individual collectible sprites from a sprite sheet
- Same technique used for character sprite sheet segmentation
- Automatically filters out noise and detects individual items
- Converts each sprite to a base64 data URL for embedding in the game

### 2. Random Spawn Positioning
- Automatically generates spawn positions on top of detected platforms
- Ensures minimum spacing between collectibles (80px default)
- Places 10-15 collectibles depending on the number of platforms
- Randomly selects which collectible sprite to use at each position

### 3. Collision Detection
- Phaser.js overlap detection between player and collectibles
- When player touches a collectible:
  - Collectible scales up and fades out
  - Collectible is destroyed
  - Collection count is tracked
  - Console logs the collection event

### 4. Visual Effects
- **Floating animation**: Collectibles bob up and down
- **Rotation animation**: Collectibles slowly rotate
- Both animations use tweens for smooth motion

## Implementation Details

### Backend Changes

#### `backend/main.py`
1. Added `collectible_url` to `GenerateGameRequest` model (Optional field)
2. Created `segment_collectible_sprites()` function:
   - Uses scipy's `ndimage.label()` for connected component analysis
   - Extracts bounding boxes for each detected sprite
   - Returns list of base64 data URLs
3. Created `generate_collectible_positions()` function:
   - Takes platform data and generates random positions
   - Ensures minimum spacing between items
   - Returns list of {x, y, sprite_index} dictionaries
4. Updated `/generate-game` endpoint:
   - Downloads collectible sprite sheet if URL provided
   - Segments sprites using connected component analysis
   - Generates positions on platforms after platform detection
   - Passes collectibles to HTML generator

#### `backend/scene_builder/web_exporter.py`
1. Updated `_generate_html()` signature to accept:
   - `collectible_sprites`: List of base64 data URLs
   - `collectible_positions`: List of position dictionaries
2. Added collectible loading in `preload()` method:
   - Loads each collectible sprite as a separate image texture
   - Uses data URIs for compatibility
3. Added collectible creation in `create()` method:
   - Creates physics group for collectibles
   - Spawns collectibles at generated positions
   - Applies floating and rotation animations
   - Sets up overlap detection with player
4. Added `collectItem()` method:
   - Handles collision between player and collectible
   - Animates collection (scale up + fade out)
   - Destroys collectible and increments counter

#### `backend/game_generator.py`
1. Updated `generate_game_html_with_urls()` signature:
   - Added `collectible_sprites` and `collectible_positions` parameters
2. Passes collectibles to `_generate_html()` when generating game

### Frontend Changes

#### `frontend/src/pages/GameSandbox.tsx`
1. Updated API call to include `collectible_url`:
   - Reads from `generatedImages.collectible` in context
   - Passes to backend as `collectible_url` field

#### `frontend/src/context/AssetContext.tsx`
- Already had `collectible` field in `GeneratedAssetImages` interface
- No changes needed

#### `frontend/src/pages/GenerateAssets.tsx`
- Already collects collectible URL and saves to context
- No changes needed

## Algorithm: Connected Component Analysis

The segmentation uses the same algorithm as character sprite extraction:

```python
# 1. Convert image to binary mask
alpha = np.array(sprite_sheet)[:, :, 3]
content_mask = alpha > 10  # True where non-transparent

# 2. Label connected components
structure = np.ones((3, 3), dtype=int)  # 8-connectivity
labeled_array, num_components = ndimage.label(content_mask, structure=structure)

# 3. Extract bounding box for each component
for i in range(1, num_components + 1):
    component_mask = labeled_array == i
    rows, cols = np.where(component_mask)
    min_row, max_row = rows.min(), rows.max()
    min_col, max_col = cols.min(), cols.max()
    # Crop sprite using bounding box
    sprite = sprite_sheet.crop((min_col, min_row, max_col+1, max_row+1))

# 4. Filter out noise (components < 1% of largest)
max_area = max(component['area'] for component in components)
filtered = [c for c in components if c['area'] > max_area * 0.01]
```

This approach:
- Works with any sprite sheet layout (grid, horizontal, scattered)
- Handles sprites with internal gaps (e.g., rings, donuts)
- Automatically filters out noise/artifacts
- Sorts sprites left-to-right for consistency

## Spawn Position Algorithm

```python
# 1. Pick random platform
platform = random.choice(platforms)

# 2. Generate random x position with margin
x = random.randint(platform['x'] + 30, platform['x'] + platform['width'] - 30)

# 3. Position above platform
y = platform['y'] - 20  # 20px above surface

# 4. Check spacing from existing collectibles
for placed_x, placed_y in placed_positions:
    distance = sqrt((x - placed_x)^2 + (y - placed_y)^2)
    if distance < 80:  # Too close
        reject and retry

# 5. Assign random sprite from segmented sprites
sprite_index = random.randint(0, num_sprites-1)
```

## Testing

A test script is provided: `backend/test_collectible_segmentation.py`

Usage:
```bash
cd backend
python test_collectible_segmentation.py path/to/collectible_spritesheet.png
```

This will:
- Load the image
- Run connected component analysis
- Print the number of sprites detected
- Show details for each sprite (position, size, area)

## Game Flow

1. User generates assets (character, background, collectible)
2. User presses "Generate Game Sandbox"
3. Frontend sends all 3 URLs to `/generate-game` endpoint
4. Backend:
   - Downloads all images
   - Analyzes background for platforms
   - Processes character sprite
   - **Segments collectible sprite sheet**
   - **Generates spawn positions on platforms**
   - Embeds everything in HTML game
5. Frontend displays playable game with collectibles

## Collision Detection in Phaser

```javascript
// In create() method:
this.collectibles = this.physics.add.group();
// ... spawn collectibles ...

this.physics.add.overlap(
    this.player,
    this.collectibles,
    this.collectItem,  // Callback function
    null,
    this
);

// Callback when player touches collectible:
collectItem(player, collectible) {
    // Visual feedback
    this.tweens.add({
        targets: collectible,
        scale: { from: collectible.scale, to: collectible.scale * 1.5 },
        alpha: { from: 1, to: 0 },
        duration: 200,
        onComplete: () => {
            collectible.destroy();
            this.collectedCount++;
        }
    });
}
```

## Future Enhancements

Possible improvements:
- [ ] Add sound effects for collection
- [ ] Display collection counter in HUD
- [ ] Different collectible types (coins, gems, powerups)
- [ ] Collectible value/scoring system
- [ ] Particle effects on collection
- [ ] Achievement for collecting all items
- [ ] Respawning collectibles
- [ ] Collectible-triggered events (unlock doors, etc.)

## Files Modified

- `backend/main.py` - Added segmentation, positioning, and endpoint logic
- `backend/scene_builder/web_exporter.py` - Updated HTML generation
- `backend/game_generator.py` - Updated method signature
- `frontend/src/pages/GameSandbox.tsx` - Pass collectible URL
- `backend/test_collectible_segmentation.py` - New test script

## Dependencies

No new dependencies required. Uses existing:
- `scipy` (for `ndimage.label`)
- `numpy`
- `PIL/Pillow`
- Phaser.js (frontend, already used)

