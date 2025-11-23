# Status Bar System Implementation

## Overview
Implemented a dynamic status bar system that tracks player health and automatically displays relevant stats (Score, Gold, Energy) based on the collectibles in the game.

## Features

### 1. Health Bar (Always Visible)
- **Position**: Top-right corner of screen
- **Max HP**: 100
- **Visual**: Red gradient bar with current/max display
- **Updates**: Real-time when collecting health items

### 2. Dynamic Stats Tracking
- **Automatic Detection**: Analyzes collectible metadata to determine which stats to track
- **Score**: Displays if any collectible gives points/score
- **Gold**: Displays if any collectible gives gold/coins
- **Energy**: Displays if any collectible gives energy
- **Only shows relevant stats**: Empty stats are hidden

### 3. Collectible Effects
- **Health Restoration**: Items like potions can restore 25 HP, 50 HP, or Full Health
- **Score/Points**: Items add to score counter
- **Gold/Coins**: Items add to gold counter
- **Energy**: Items add to energy counter

## UI Layout

```
┌─────────────────────────────────┐
│  Status Bar (Top-Right)         │
├─────────────────────────────────┤
│  HEALTH                         │
│  ████████████████░░░░  75 / 100 │
│                                 │
│  SCORE              250         │
│  GOLD               35          │
│  ENERGY             75          │
└─────────────────────────────────┘
```

## Implementation Details

### Backend: Claude Vision Prompt Enhancement

Updated `analyze_collectible_metadata()` to guide Claude on status effects:

```python
2. **Status Effect**: A relevant gameplay effect this collectible provides
   - For scoring/currency: "+10 Score", "Gold +50", "+25 Points"
   - For health (ONLY if item looks like food, potion, heart, or medical): 
     "Restores 25 HP", "Restores 50 HP"
   - For other effects: "Speed Boost", "Double Jump", "Shield", "Extra Life"
   - Health (HP) maxes out at 100, so restoration amounts should be 25, 50, or "Full Health"
```

**Examples of Valid Status Effects:**
- "Score +10"
- "Gold +50"
- "Restores 25 HP"
- "Restores 50 HP"
- "Full Health"
- "Energy +25"
- "Speed Boost"
- "Double Jump"

### Frontend: Status Bar HTML/CSS

**Added CSS Styles:**
```css
#status-bar {
    position: fixed;
    top: 20px;
    right: 20px;
    background: rgba(0, 0, 0, 0.8);
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 12px;
    padding: 15px 20px;
    min-width: 250px;
    z-index: 999;
}

.health-bar-container {
    width: 100%;
    height: 20px;
    background: rgba(255, 0, 0, 0.2);
    border: 2px solid #8B0000;
    border-radius: 10px;
}

.health-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, #FF0000 0%, #FF6B6B 100%);
    transition: width 0.3s ease;
}
```

**HTML Structure:**
```html
<div id="status-bar">
    <div class="stat-row">
        <div class="stat-label">Health</div>
    </div>
    <div class="health-bar-container">
        <div class="health-bar-fill"></div>
        <div class="health-bar-text">100 / 100</div>
    </div>
    <div id="dynamic-stats"></div>
</div>
```

### Phaser Game Logic

**1. Initialize Player Stats (in `create()`):**
```javascript
this.playerHealth = 100;
this.playerMaxHealth = 100;
this.playerStats = {
    score: 0,
    gold: 0,
    energy: 0
};
```

**2. Analyze Collectible Metadata (in `preload()`):**
```javascript
analyzeCollectibleStats(metadata) {
    const stats = {};
    
    metadata.forEach(item => {
        const effect = item.status_effect || '';
        const effectLower = effect.toLowerCase();
        
        if (effectLower.includes('score') || effectLower.includes('point')) {
            stats.score = true;
        }
        if (effectLower.includes('gold') || effectLower.includes('coin')) {
            stats.gold = true;
        }
        if (effectLower.includes('energy')) {
            stats.energy = true;
        }
    });
    
    return stats;
}
```

**3. Apply Collectible Effects (in `collectItem()`):**
```javascript
applyCollectibleEffect(statusEffect) {
    const effectLower = statusEffect.toLowerCase();
    const numberMatch = statusEffect.match(/[+]?(\d+)/);
    const value = numberMatch ? parseInt(numberMatch[1]) : 0;
    
    // Health restoration (max 100)
    if (effectLower.includes('restore') && 
        (effectLower.includes('hp') || effectLower.includes('health'))) {
        this.playerHealth = Math.min(this.playerMaxHealth, this.playerHealth + value);
    } else if (effectLower.includes('full health')) {
        this.playerHealth = this.playerMaxHealth;
    }
    // Score/Points
    else if (effectLower.includes('score') || effectLower.includes('point')) {
        this.playerStats.score += value || 10;
    }
    // Gold/Coins
    else if (effectLower.includes('gold') || effectLower.includes('coin')) {
        this.playerStats.gold += value || 1;
    }
    // Energy
    else if (effectLower.includes('energy')) {
        this.playerStats.energy += value || 25;
    }
    
    this.updateStatusBar();
}
```

**4. Update Status Bar Display:**
```javascript
updateStatusBar() {
    // Update health bar
    const healthPercent = (this.playerHealth / this.playerMaxHealth) * 100;
    healthFill.style.width = healthPercent + '%';
    healthText.textContent = this.playerHealth + ' / ' + this.playerMaxHealth;
    
    // Update dynamic stats (only show tracked stats)
    let statsHTML = '';
    
    if (this.trackedStats.score) {
        statsHTML += `<div class="stat-row">
            <div class="stat-label">Score</div>
            <div class="stat-value">` + this.playerStats.score + `</div>
        </div>`;
    }
    
    if (this.trackedStats.gold) {
        statsHTML += `<div class="stat-row">
            <div class="stat-label">Gold</div>
            <div class="stat-value">` + this.playerStats.gold + `</div>
        </div>`;
    }
    
    if (this.trackedStats.energy) {
        statsHTML += `<div class="stat-row">
            <div class="stat-label">Energy</div>
            <div class="stat-value">` + this.playerStats.energy + `</div>
        </div>`;
    }
    
    dynamicStatsContainer.innerHTML = statsHTML;
}
```

## Data Flow

```
1. Collectible Metadata Generated
   └─> Claude Vision identifies items and effects
       └─> Example: "Restores 25 HP", "Gold +50", "Score +10"

2. Game Loads
   └─> analyzeCollectibleStats() scans metadata
       └─> Determines: {score: true, gold: true}
       └─> Health bar always shown

3. Status Bar Initialized
   └─> Shows health: 100/100
   └─> Shows only relevant stats: Score, Gold
   └─> Energy hidden (not used by any collectible)

4. Player Collects Item
   └─> collectItem() called
       └─> applyCollectibleEffect() parses status_effect
           ├─> "Gold +50" → playerStats.gold += 50
           ├─> "Restores 25 HP" → playerHealth += 25 (max 100)
           └─> "Score +10" → playerStats.score += 10
       └─> updateStatusBar() refreshes display
           └─> Health bar animates
           └─> Gold counter updates
           └─> Score counter updates
```

## Effect Parsing Logic

The system uses smart pattern matching to parse status effects:

### Numeric Value Extraction
```javascript
const numberMatch = statusEffect.match(/[+]?(\d+)/);
const value = numberMatch ? parseInt(numberMatch[1]) : 0;
```

**Examples:**
- "Gold +50" → value = 50
- "Restores 25 HP" → value = 25
- "Score +10" → value = 10

### Effect Type Detection
```javascript
const effectLower = statusEffect.toLowerCase();

if (effectLower.includes('restore') && effectLower.includes('hp')) {
    // Health restoration
} else if (effectLower.includes('score') || effectLower.includes('point')) {
    // Score
} else if (effectLower.includes('gold') || effectLower.includes('coin')) {
    // Gold
}
```

**Pattern Matching:**
- Health: "restore", "hp", "health", "full health"
- Score: "score", "point", "points"
- Gold: "gold", "coin", "coins"
- Energy: "energy"

## Health System

### Rules
- **Starting HP**: 100
- **Maximum HP**: 100
- **Restoration**: Adds to current HP, capped at 100
- **Full Health**: Sets HP to 100 regardless of current

### Examples
```javascript
// Current HP: 60
"Restores 25 HP" → HP becomes 85
"Restores 50 HP" → HP becomes 100 (capped)
"Full Health" → HP becomes 100

// Current HP: 90
"Restores 25 HP" → HP becomes 100 (capped)
"Full Health" → HP becomes 100
```

## Dynamic Stats Display

### Visibility Rules
Only stats that are **actually used** by collectibles are displayed:

**Scenario 1: Scoring Game**
- Collectibles: Coins (+10 Score each)
- Status Bar Shows: Health, Score
- Hidden: Gold, Energy

**Scenario 2: RPG-Style Game**  
- Collectibles: Health Potions, Gold Coins, Energy Crystals
- Status Bar Shows: Health, Gold, Energy
- Hidden: Score

**Scenario 3: Simple Platformer**
- Collectibles: Power-ups (no stat effects)
- Status Bar Shows: Health only
- Hidden: Score, Gold, Energy

## Visual Design

### Color Scheme
- **Background**: Dark (rgba(0, 0, 0, 0.8))
- **Border**: White semi-transparent
- **Health Bar**: Red gradient (#FF0000 → #FF6B6B)
- **Labels**: White uppercase
- **Values**: Gold (#FFD700)

### Positioning
- **Location**: Fixed top-right (20px from top, 20px from right)
- **Z-Index**: 999 (above game, below notifications)
- **Width**: Minimum 250px, expands as needed

### Animations
- **Health Bar**: Smooth width transition (0.3s ease)
- **Stats**: Instant update (no animation for clarity)

## Console Logging

Detailed logs for debugging:

```javascript
// On game load
"Tracked stats: {score: true, gold: true}"

// On collection
"Gold increased by 50. Total: 150"
"Health restored by 25. Current: 85"
"Score increased by 10. Total: 120"
"Collected 'Golden Treasure Coin' (Gold +50)! Total: 5"
```

## Files Modified

1. **`backend/main.py`**
   - Enhanced Claude Vision prompt with HP guidelines
   - Added examples for Score, Gold, Energy, HP restoration

2. **`backend/scene_builder/web_exporter.py`**
   - Added status bar CSS styling
   - Added status bar HTML structure
   - Added `analyzeCollectibleStats()` method
   - Added `applyCollectibleEffect()` method
   - Added `updateStatusBar()` method
   - Initialized player stats in `create()`
   - Modified `collectItem()` to apply effects

## Benefits

1. **Automatic Adaptation**: Status bar adapts to game type automatically
2. **Clean UI**: Only shows relevant information
3. **Health Tracking**: Visual health bar with precise HP display
4. **Multiple Currencies**: Supports Score, Gold, Energy simultaneously
5. **Smart Parsing**: Flexible effect parsing handles various formats
6. **HP Cap Enforcement**: Prevents health from exceeding 100
7. **Real-time Updates**: Immediate visual feedback on collection

## Summary

The status bar system provides comprehensive player stat tracking with automatic detection of relevant stats based on collectible metadata. Health is always displayed with a visual bar, while Score, Gold, and Energy only appear if collectibles in the game provide them. The system intelligently parses status effect strings to apply appropriate stat changes and health restoration, with HP capped at 100.

