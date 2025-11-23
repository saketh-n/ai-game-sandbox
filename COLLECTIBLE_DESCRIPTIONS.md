# Collectible Descriptions Feature

## Overview
Added intelligent collectible identification and descriptions using Claude Vision API. When a player collects an item in the game, a notification displays showing the collectible's name and a fun description.

## How It Works

### 1. Claude Vision Analysis
**Before sprite segmentation**, the collectible sprite sheet is analyzed by Claude Vision API to identify each collectible and generate metadata.

**API Call:**
```python
analyze_collectible_metadata(collectible_path, anthropic_client)
```

**Prompt to Claude:**
```
Analyze this sprite sheet of collectible items for a video game.

Looking at the image from LEFT TO RIGHT, identify each collectible item and provide:
1. A short name (1-3 words, like "Gold Coin", "Magic Gem", "Health Potion")
2. A fun, engaging description (1-2 sentences that a player would see when collecting it)

Respond in JSON format:
{
  "collectibles": [
    {
      "name": "Item Name",
      "description": "A brief, exciting description."
    }
  ]
}
```

**Example Response:**
```json
{
  "collectibles": [
    {
      "name": "Golden Coin",
      "description": "A shimmering gold coin worth 10 points. Collect them all!"
    },
    {
      "name": "Magic Crystal",
      "description": "A mysterious glowing crystal that restores your energy."
    },
    {
      "name": "Ruby Gem",
      "description": "A rare precious gem! This one's worth big points."
    }
  ]
}
```

### 2. Correlation with Sprites
The metadata is correlated with segmented sprites using **positional order**:

- **Claude Vision** identifies collectibles **left-to-right**
- **Sprite Segmentation** extracts sprites **left-to-right** (sorted by x-position)
- **Result**: `collectible_metadata[0]` corresponds to `collectible_sprites[0]`, etc.

### 3. Storage in Game
Metadata is passed to the Phaser game along with sprite data:

```javascript
const collectibleMetadata = [
  {name: "Golden Coin", description: "A shimmering gold coin..."},
  {name: "Magic Crystal", description: "A mysterious glowing crystal..."},
  ...
];
```

Each collectible sprite stores its index:
```javascript
collectible.setData('spriteIndex', spriteIndex);
```

### 4. Display on Collection
When player collects an item:

```javascript
collectItem(player, collectible) {
    const spriteIndex = collectible.getData('spriteIndex');
    const metadata = this.collectibleMetadata[spriteIndex];
    
    showCollectibleNotification(metadata.name, metadata.description);
    
    // ... animate and destroy collectible ...
}
```

### 5. UI Notification
A notification appears at the top of the screen:

```
┌─────────────────────────────────────────┐
│          GOLDEN COIN                    │
│  A shimmering gold coin worth 10 points │
└─────────────────────────────────────────┘
```

- **Duration**: 3 seconds
- **Style**: Gradient purple background, white text
- **Animation**: Fade in/out
- **Position**: Top center, fixed

## Implementation Details

### Backend Changes

#### 1. `backend/main.py`

**New Function: `analyze_collectible_metadata()`**
```python
def analyze_collectible_metadata(collectible_path: Path, anthropic_client) -> List[dict]:
    """Use Claude Vision to identify each collectible and get name + description"""
    # Load and encode image as base64
    # Call Claude Vision API with prompt
    # Parse JSON response
    # Return list of {name, description} dicts
```

**Updated `/generate-game` endpoint:**
```python
# Step 1: Analyze metadata
collectible_metadata = await asyncio.to_thread(
    analyze_collectible_metadata,
    coll_path,
    client
)

# Step 2: Segment sprites
collectible_sprites = await asyncio.to_thread(
    segment_collectible_sprites,
    coll_path,
    game_gen.sprite_analyzer
)

# Step 3: Verify counts match (pad if needed)
if len(collectible_metadata) != len(collectible_sprites):
    # Pad with generic entries
    while len(collectible_metadata) < len(collectible_sprites):
        collectible_metadata.append({
            "name": f"Collectible {idx + 1}",
            "description": "A mysterious collectible item!"
        })

# Step 4: Pass to game generator
game_html = game_gen.web_exporter._generate_html(
    ...,
    collectible_sprites,
    collectible_positions,
    collectible_metadata  # NEW
)
```

#### 2. `backend/game_generator.py`

**Updated signature:**
```python
def generate_game_html_with_urls(
    ...,
    collectible_sprites: list = None,
    collectible_positions: list = None,
    collectible_metadata: list = None  # NEW
) -> tuple[str, Dict[str, Any], list[str]]:
```

**Passes metadata to web_exporter:**
```python
game_html = self.web_exporter._generate_html(
    ...,
    collectible_sprites,
    collectible_positions,
    collectible_metadata
)
```

#### 3. `backend/scene_builder/web_exporter.py`

**Updated signature:**
```python
def _generate_html(
    ...,
    collectible_sprites: list = None,
    collectible_positions: list = None,
    collectible_metadata: list = None  # NEW
) -> str:
```

**Embeds metadata in HTML:**
```python
collectible_metadata_json = json.dumps(collectible_metadata if collectible_metadata else [])
```

**Added CSS for notification:**
```css
#collectible-notification {
    position: fixed;
    top: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 15px 30px;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    font-size: 1.1rem;
    font-weight: bold;
    z-index: 1000;
    opacity: 0;
    transition: opacity 0.3s ease;
}

#collectible-notification.show {
    opacity: 1;
}
```

**Added HTML element:**
```html
<div id="collectible-notification">
    <div class="notification-name"></div>
    <div class="notification-description"></div>
</div>
```

**Phaser: Load metadata:**
```javascript
const collectibleMetadata = {collectible_metadata_json};
this.collectibleMetadata = collectibleMetadata;
```

**Phaser: Store sprite index:**
```javascript
collectible.setData('spriteIndex', spriteIndex);
```

**Phaser: Updated `collectItem()`:**
```javascript
collectItem(player, collectible) {
    const spriteIndex = collectible.getData('spriteIndex');
    const metadata = this.collectibleMetadata[spriteIndex];
    const name = metadata ? metadata.name : 'Collectible';
    const description = metadata ? metadata.description : 'You found something!';
    
    this.showCollectibleNotification(name, description);
    
    // ... animate and destroy ...
}
```

**Phaser: New method `showCollectibleNotification()`:**
```javascript
showCollectibleNotification(name, description) {
    const notification = document.getElementById('collectible-notification');
    const nameEl = notification.querySelector('.notification-name');
    const descEl = notification.querySelector('.notification-description');
    
    nameEl.textContent = name;
    descEl.textContent = description;
    
    notification.classList.add('show');
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}
```

## Data Flow

```
Collectible Sprite Sheet (PNG)
        ↓
Claude Vision API (identify & describe)
        ↓
collectible_metadata: [
  {name: "Item 1", description: "..."},
  {name: "Item 2", description: "..."}
]
        ↓
Sprite Segmentation (extract individual sprites)
        ↓
collectible_sprites: [
  "data:image/png;base64,...",  // Item 1
  "data:image/png;base64,..."   // Item 2
]
        ↓
Both arrays indexed in parallel (same left-to-right order)
        ↓
Game HTML Generation (embed metadata JSON)
        ↓
Phaser Game Loads:
  - Sprites as textures
  - Metadata as array
        ↓
Collectible Spawning:
  - Each collectible stores its sprite index
  - collectible.setData('spriteIndex', i)
        ↓
Player Collects Item:
  - Get sprite index from collectible
  - Look up metadata[spriteIndex]
  - Display notification with name & description
        ↓
UI Notification (3 seconds)
  - Name in large text
  - Description below
  - Fade in/out animation
```

## Order Correlation Example

**Input Sprite Sheet:**
```
┌────────────────────────────────────────┐
│  🪙     💎     ⭐     🔑     ❤️         │
│  0      1      2      3      4          │
└────────────────────────────────────────┘
```

**Claude Vision Output (left-to-right):**
```json
[
  {name: "Gold Coin", description: "..."},      // 0
  {name: "Diamond", description: "..."},        // 1
  {name: "Star", description: "..."},           // 2
  {name: "Key", description: "..."},            // 3
  {name: "Heart", description: "..."}           // 4
]
```

**Sprite Segmentation Output (left-to-right):**
```javascript
[
  "data:image/png;base64,🪙...",  // 0
  "data:image/png;base64,💎...",  // 1
  "data:image/png;base64,⭐...",  // 2
  "data:image/png;base64,🔑...",  // 3
  "data:image/png;base64,❤️..."   // 4
]
```

**In-Game Spawning:**
```javascript
// Random selection: sprite index 2 (Star)
collectible.texture = 'collectible_2';  // ⭐ sprite
collectible.setData('spriteIndex', 2);
```

**On Collection:**
```javascript
spriteIndex = collectible.getData('spriteIndex');  // 2
metadata = collectibleMetadata[2];  // {name: "Star", description: "..."}
showNotification("Star", "...");
```

## Error Handling

### Metadata Count Mismatch
If Claude Vision detects a different number of collectibles than sprite segmentation:

```python
if len(collectible_metadata) != len(collectible_sprites):
    logger.warning(f"Mismatch: {len(collectible_metadata)} metadata vs {len(collectible_sprites)} sprites")
    
    # Pad with generic entries
    while len(collectible_metadata) < len(collectible_sprites):
        collectible_metadata.append({
            "name": f"Collectible {idx + 1}",
            "description": "A mysterious collectible item!"
        })
```

### Missing Metadata
If metadata is missing for a sprite:

```javascript
const metadata = this.collectibleMetadata[spriteIndex];
const name = metadata ? metadata.name : 'Collectible';
const description = metadata ? metadata.description : 'You found something!';
```

### Claude Vision API Failure
If the API call fails:

```python
try:
    collectibles_data = json.loads(response_text)
    return collectibles_data.get("collectibles", [])
except Exception as e:
    logger.error(f"Error analyzing collectible metadata: {e}")
    return []  # Empty list as fallback
```

Result: All collectibles get generic names and descriptions.

## Benefits

1. **Dynamic Content**: Each collectible automatically gets a unique name and description
2. **Thematic Consistency**: Claude understands the visual style and generates appropriate descriptions
3. **Enhanced Player Experience**: Notifications make collecting items more engaging
4. **Zero Manual Work**: No need to manually label each collectible
5. **Flexible**: Works with any collectible sprite sheet
6. **Fallback Handling**: Gracefully handles mismatches or API failures

## Future Enhancements

- [ ] Add sound effects on collection
- [ ] Track collection stats (X/Y collected)
- [ ] Display collected items in an inventory UI
- [ ] Different notification styles per collectible type
- [ ] Collectible rarity system (common, rare, legendary)
- [ ] Achievement notifications for collecting all items
- [ ] Multiple languages for descriptions

## Testing

To test:
1. Generate a game with a collectible sprite sheet
2. Play the game and collect an item
3. Verify notification appears with correct name and description
4. Check console logs for debugging info

**Console Output:**
```
Collectible metadata: [
  {name: "Golden Coin", description: "..."},
  ...
]
Collected "Golden Coin"! Total: 1
```

## Summary

This feature uses Claude Vision API to automatically identify and describe collectibles before segmentation, correlates metadata with sprites using left-to-right ordering, and displays engaging notifications when players collect items. The implementation is robust with fallback handling and enhances the player experience with zero manual labeling required.

