# AI Video Game Asset Generator - Feature Overview

## 🎯 What This Does

This application takes a video game theme/description and uses Claude AI to generate **detailed, ready-to-use prompts** for image generation models (like Stable Diffusion, Midjourney, DALL-E, etc.).

## 📦 Generated Asset Categories

### 1. Main Character 🎮
- **Description**: Brief overview of the protagonist
- **Variations**: 4-5 detailed prompt variations for different poses/states
  - Idle stance
  - Action pose
  - Special attack
  - Running/movement
  - Powered-down/alternate form

### 2. Environment Assets 🌍
Organized into specific categories with multiple variations each:
- **Ground Tiles**: Seamless, tileable textures
- **Floating Platforms**: Various styles (stone, energy, cloud)
- **Collectibles**: Crystals, power-ups, items
- **Props**: Training posts, rocks, trees, grass
- **Buildings**: Architecture matching the game theme
- **Key Elements List**: Shows what environmental assets are needed

### 3. NPCs 👥
Categorized by role:
- **Allies**: Friendly characters, mentors, companions
- **Enemies**: Various threat levels (grunts, mini-bosses, bosses)
- **Neutral**: Merchants, villagers, quest-givers

### 4. Background Scenes 🎨
Full scene compositions for:
- Level backgrounds (parallax-ready)
- Menu/title screens
- Boss arenas
- Hub areas
- Different biomes/locations

## 🎨 UI Features

### Collapsible Sections
- Each major category can be expanded/collapsed
- Nested subsections for environment assets and NPC categories
- Clean, organized hierarchy

### Editable Text Areas
- Every prompt is in an editable textarea
- Modify prompts in real-time
- Changes are preserved in component state
- Monospace font for easy reading

### Copy Functionality
- Each prompt has a "Copy" button
- One-click copy to clipboard
- Use directly in your image generation tool

### Visual Design
- **Glassmorphism**: Frosted glass effects with backdrop blur
- **Gradient Background**: Purple/indigo/blue gaming aesthetic
- **Color-Coded**: Different sections use subtle color variations
- **Icons**: Emoji icons for quick visual identification
- **Badges**: Key elements displayed as pill badges
- **Animations**: Smooth transitions and fade-ins

## 🔧 Technical Implementation

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── App.tsx                          # Main app component
│   ├── components/
│   │   └── AssetPromptsDisplay.tsx     # Structured data display
│   ├── main.tsx                         # Entry point
│   └── index.css                        # Global styles + animations
├── package.json
└── vite.config.ts
```

**Key Components:**
- `App.tsx`: Handles API calls, loading states, error handling
- `AssetPromptsDisplay.tsx`: Renders structured JSON with collapsible sections

### Backend (Python + FastAPI)
```
backend/
├── main.py              # FastAPI server with Claude integration
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variable template
└── logs/               # Application logs
```

**Key Features:**
- Claude Sonnet 4.5 integration
- Structured JSON prompt engineering
- Comprehensive error handling
- Request logging with unique IDs
- CORS configuration for local development

## 📝 Prompt Structure

The backend returns a JSON object with this structure:

```typescript
{
  main_character: {
    description: string,
    variations: string[]
  },
  environment_assets: {
    key_elements_needed: string[],
    assets: {
      [asset_name]: {
        variations: string[]
      }
    }
  },
  npcs: {
    categories: {
      allies: { variations: string[] },
      enemies: { variations: string[] },
      neutral: { variations: string[] }
    }
  },
  backgrounds: {
    scenes: string[]
  }
}
```

## 🎮 Example Workflow

1. User enters: "Dragon Ball Z style fighting game"
2. Claude generates:
   - Main character prompts for a Super Saiyan warrior
   - Environment: wasteland tiles, energy crystals, training posts
   - NPCs: Master Roshi (ally), Frieza (enemy), Tournament announcer (neutral)
   - Backgrounds: Hyperbolic Time Chamber, World Tournament arena
3. User can:
   - Expand/collapse each section
   - Edit any prompt to refine details
   - Copy individual prompts to use in Midjourney/Stable Diffusion
   - Generate multiple game assets systematically

## 🚀 Usage Tips

1. **Be Specific**: Include art style, genre, and mood in your theme
2. **Iterate**: Use the edit feature to refine prompts
3. **Copy & Generate**: Use the copy button to quickly move prompts to your image generator
4. **Organize**: The structure helps you systematically generate all needed assets
5. **Consistency**: All prompts maintain the same art style and theme

## 🔮 Future Enhancement Ideas

- [ ] Export all prompts to JSON file
- [ ] Save/load prompt sets
- [ ] Direct integration with image generation APIs
- [ ] Preview generated images in-app
- [ ] Batch generation
- [ ] Custom prompt templates
- [ ] Asset variation generator (reroll specific assets)
- [ ] Game engine export formats (Unity, Godot, etc.)

