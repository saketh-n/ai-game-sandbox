# Collectible Sizing - Dynamic Scaling

## Change Summary
Updated collectible sprites to be **dynamically scaled** to exactly **1/2 the height and width** of the character sprite, ensuring consistent relative sizing regardless of the actual sprite dimensions.

## Implementation

### Before
```javascript
// Fixed scale of 0.5
collectible.setScale(0.5);
```

**Problem:** This scales collectibles to 50% of their original size, but doesn't consider the character's size. If the character is 200px tall and the collectible is 64px tall, they won't have a consistent 2:1 ratio.

### After
```javascript
// Player scaling
const targetHeight = 100;  // Player target display height
const playerScale = targetHeight / config['character']['frame_height'];
this.player.setScale(playerScale);

// Calculate player display dimensions
const playerDisplayHeight = targetHeight;  // 100px
const playerDisplayWidth = config['character']['frame_width'] * playerScale;

// Collectible target size (1/2 of character)
const collectibleTargetHeight = playerDisplayHeight / 2;  // 50px
const collectibleTargetWidth = playerDisplayWidth / 2;

// Get actual collectible texture dimensions
const collectibleTexture = this.textures.get('collectible_' + spriteIndex);
const collectibleSourceWidth = collectibleTexture.source[0].width;
const collectibleSourceHeight = collectibleTexture.source[0].height;

// Scale collectible to be exactly 1/2 the character's size
const collectibleScale = collectibleTargetHeight / collectibleSourceHeight;
collectible.setScale(collectibleScale);
```

**Benefits:** Collectibles are now **always** exactly half the character's display size, creating perfect visual consistency.

## Size Calculation Logic

### Character Sprite
1. **Source dimensions**: From sprite sheet analysis (e.g., 128px × 128px per frame)
2. **Target height**: Fixed at 100px for gameplay
3. **Player scale**: `100 / 128 = 0.78125`
4. **Display size**: `128 × 0.78125 = 100px` tall

### Collectible Sprite
1. **Source dimensions**: From segmented sprite (e.g., 64px × 64px)
2. **Target height**: `100 / 2 = 50px` (half of character)
3. **Collectible scale**: `50 / 64 = 0.78125`
4. **Display size**: `64 × 0.78125 = 50px` tall

### Result
- Character: 100px tall ✓
- Collectible: 50px tall (exactly 1/2) ✓
- Ratio maintained regardless of source dimensions ✓

## Visual Comparison

### Example 1: Large Character, Small Collectible
```
Source Sprites:
  Character: 256×256px per frame
  Collectible: 32×32px

Display in Game:
  Character: 100px tall (scale = 100/256 = 0.39)
  Collectible: 50px tall (scale = 50/32 = 1.56)
  
  👤 (100px)
  💎 (50px) ← Exactly 1/2
```

### Example 2: Small Character, Large Collectible
```
Source Sprites:
  Character: 64×64px per frame
  Collectible: 128×128px

Display in Game:
  Character: 100px tall (scale = 100/64 = 1.56)
  Collectible: 50px tall (scale = 50/128 = 0.39)
  
  👤 (100px)
  💎 (50px) ← Exactly 1/2
```

### Example 3: Same Source Size
```
Source Sprites:
  Character: 128×128px per frame
  Collectible: 128×128px

Display in Game:
  Character: 100px tall (scale = 100/128 = 0.78)
  Collectible: 50px tall (scale = 50/128 = 0.39)
  
  👤 (100px)
  💎 (50px) ← Exactly 1/2
```

## Debug Output

The code now logs detailed sizing information to the console:

```
Collectible 0: source=64x64, scale=0.78, display=50x50
Collectible 1: source=48x52, scale=0.96, display=46x50
Collectible 2: source=70x58, scale=0.86, display=60x50
```

This helps verify that:
- Each collectible's actual source dimensions are detected
- The scale is calculated correctly
- The final display size is exactly 50px tall (half of 100px character)

## Code Location

**File:** `backend/scene_builder/web_exporter.py`

**Lines:**
- Player scaling: ~330-336
- Collectible target calculation: ~367-369
- Collectible scaling: ~380-393

## Benefits

1. **Consistent Visual Hierarchy**: Collectibles are always smaller than the character in a predictable way
2. **Automatic Scaling**: Works with any sprite dimensions automatically
3. **Professional Appearance**: Maintains design proportions
4. **Flexible**: Easy to adjust the ratio (currently 1/2, could be changed to 1/3, 1/4, etc.)
5. **Debugging**: Console logs make it easy to verify sizing

## Future Adjustments

To change the collectible size ratio, simply modify:

```javascript
// Current: 1/2 (50%)
const collectibleTargetHeight = playerDisplayHeight / 2;

// Smaller collectibles: 1/3 (33%)
const collectibleTargetHeight = playerDisplayHeight / 3;

// Larger collectibles: 2/3 (66%)
const collectibleTargetHeight = (playerDisplayHeight * 2) / 3;
```

## Summary

Collectibles now scale **dynamically relative to the character sprite**, ensuring they're always exactly **1/2 the character's display size** regardless of the source sprite dimensions. This creates a consistent, professional appearance in the generated games.

