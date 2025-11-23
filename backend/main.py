from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from anthropic import Anthropic, APIStatusError, APIConnectionError, AuthenticationError, RateLimitError
from loguru import logger
import os
from dotenv import load_dotenv
import traceback
from typing import List, Optional
import asyncio
import json
import tempfile
import httpx
from pathlib import Path
from cache_manager import cache
from image_cache_manager import image_cache

from image_generation.generator import ImageGenerator
from image_generation.config import ImageGenerationConfig
from game_generator import GameGenerator
from sprite_processing.sprite_sheet_analyzer import SpriteSheetAnalyzer

# Load environment variables
load_dotenv()

app = FastAPI(
    title="AI Asset Generator API",
    description="Generate detailed image prompts for game assets using Claude",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup logging
logger.remove()  # Remove default handler
logger.add("logs/app.log", rotation="500 MB", retention="10 days", level="INFO")
logger.add(lambda msg: print(msg, flush=True), level="INFO")  # Console output

# Initialize Anthropic client
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
if not anthropic_api_key:
    logger.critical("ANTHROPIC_API_KEY not found in environment variables")
    raise ValueError("ANTHROPIC_API_KEY is required")

client = Anthropic(api_key=anthropic_api_key)

# Request/Response Models
class PromptRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=2000, description="Video game concept or theme description")

class PromptResponse(BaseModel):
    result: str
    cached: bool = False

class CachedPromptItem(BaseModel):
    prompt: str
    timestamp: str
    preview: str

class CachedPromptsResponse(BaseModel):
    prompts: List[CachedPromptItem]
    count: int

class FetchCachedRequest(BaseModel):
    prompt: str

class CachedResultResponse(BaseModel):
    prompt: str
    result: str
    timestamp: str

class GenerateImageRequest(BaseModel):
    prompt: str = Field(..., description="Image generation prompt")
    category: str = Field(..., description="Asset category")
    style: str = Field(default="", description="Style specification")
    additional_instructions: str = Field(default="", description="Additional generation instructions")
    image_size: str = Field(default="", description="Image size specification")
    output_format: str = Field(default="png", description="Output format")
    force_regenerate: bool = Field(default=False, description="Force regeneration, bypassing cache")

class GenerateImageResponse(BaseModel):
    image_url: str
    prompt: str
    category: str
    cached: bool = False

class GenerateGameRequest(BaseModel):
    background_url: str = Field(..., description="URL to background image")
    character_url: str = Field(..., description="URL to character sprite sheet")
    collectible_url: Optional[str] = Field(None, description="URL to collectible sprite sheet")
    num_frames: int = Field(default=8, description="Number of animation frames in sprite sheet")
    game_name: str = Field(default="GeneratedGame", description="Name for the generated game")
    debug_options: dict = Field(default={"show_sprite_frames": True, "show_platforms": False}, description="Debug visualization options")

class GenerateGameResponse(BaseModel):
    game_html: str = Field(..., description="Complete HTML game code")
    scene_config: dict = Field(..., description="Game scene configuration")
    platforms_detected: int = Field(..., description="Number of platforms detected by AI")
    gaps_detected: int = Field(..., description="Number of gaps detected")
    spawn_point: dict = Field(..., description="Character spawn coordinates")
    debug_frames: List[str] = Field(default=[], description="Base64 encoded debug frames for visualization")
    debug_platforms: str = Field(default="", description="Base64 encoded platform visualization")
    debug_collectibles: List[dict] = Field(default=[], description="Extracted collectible sprites with metadata for visualization")

image_generator = ImageGenerator(api_key=os.getenv("FAL_KEY"))


def analyze_collectible_metadata(collectible_path: Path, anthropic_client) -> List[dict]:
    """
    Use Claude Vision to identify each collectible and get name + description.
    
    Args:
        collectible_path: Path to collectible sprite sheet image
        anthropic_client: Anthropic client for API calls
        
    Returns:
        List of dicts with 'name' and 'description' for each collectible (left to right order)
    """
    import base64
    
    logger.info(f"Analyzing collectible metadata with Claude Vision...")
    
    # Load and encode image
    with open(collectible_path, 'rb') as f:
        image_data = base64.standard_b64encode(f.read()).decode('utf-8')
    
    # Determine media type
    ext = collectible_path.suffix.lower()
    media_type_map = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.webp': 'image/webp',
        '.gif': 'image/gif'
    }
    media_type = media_type_map.get(ext, 'image/png')
    
    # Create vision prompt
    prompt = """Analyze this sprite sheet of collectible items for a video game.

Looking at the image from LEFT TO RIGHT, identify each collectible item and provide:
1. **Name**: A descriptive, thematic name (2-4 words) based on what you see
   - Examples: "Golden Victory Coin", "Mystic Power Crystal", "Ancient Health Potion", "Enchanted Speed Boots"
   - Make it evocative and game-appropriate
   
2. **Status Effect**: A relevant gameplay effect this collectible provides
   **PRIORITY EFFECTS** (use these whenever possible based on item appearance):
   - **Currency items** (coins, gems, treasures, gold objects): "Gold +25", "Gold +50", "Gold +100"
   - **Score items** (stars, trophies, diamonds, special collectibles): "Score +10", "Score +25", "Score +50"
   - **Food/Health items** (fruits, potions, hearts, medical items, food): "Restores 25 HP", "Restores 50 HP", "Full Health"
   
   Other effects (use sparingly for unique items):
   - "Energy +25", "Speed Boost", "Double Jump", "Shield", "Extra Life"
   
   **GUIDELINES:**
   - Health (HP) maxes out at 100, so restoration amounts should be 25, 50, or "Full Health"
   - Match the effect value to the item's rarity/appearance (shinier/bigger = higher value)
   - Most items should give Gold, Score, or Health - these are the core gameplay mechanics
   - Be creative but clear about what it does
   
3. **Description**: A brief, exciting flavor text (1 sentence)
   - Combine the item's appearance with its effect
   - Make it fun and engaging for players

Respond in this EXACT JSON format (no markdown, just JSON):
{
  "collectibles": [
    {
      "name": "Descriptive Item Name",
      "status_effect": "What It Does",
      "description": "A single sentence combining lore and effect."
    }
  ]
}

EXAMPLES:
{
  "collectibles": [
    {
      "name": "Golden Victory Coin",
      "status_effect": "Gold +25",
      "description": "A shimmering gold coin worth a small fortune!"
    },
    {
      "name": "Ancient Treasure Gem",
      "status_effect": "Gold +100",
      "description": "A rare gemstone that glimmers with untold riches!"
    },
    {
      "name": "Ruby Score Star",
      "status_effect": "Score +50",
      "description": "A brilliant red star that boosts your score!"
    },
    {
      "name": "Crimson Health Potion",
      "status_effect": "Restores 50 HP",
      "description": "A bubbling red elixir that heals your wounds!"
    },
    {
      "name": "Fresh Apple",
      "status_effect": "Restores 25 HP",
      "description": "A crisp, juicy apple that restores your vitality!"
    },
    {
      "name": "Bronze Trophy Coin",
      "status_effect": "Score +10",
      "description": "A small trophy coin marking your achievement!"
    },
    {
      "name": "Mysterious Power Orb",
      "status_effect": "Energy +25",
      "description": "A glowing orb that surges with mystical energy!"
    }
  ]
}

IMPORTANT: 
- List items in LEFT-TO-RIGHT order as they appear in the sprite sheet
- Include ALL items you can see in the image
- Name should be descriptive and thematic (not generic like "Coin 1")
- Status effect should be a clear gameplay mechanic - PRIORITIZE Gold, Score, and Health effects
- Match the effect to the item's visual appearance (gold items = Gold, stars/trophies = Score, food/potions = Health)
- Description should be one engaging sentence"""

    try:
        # Call Claude Vision API
        message = anthropic_client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2000,
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
        
        response_text = message.content[0].text.strip()
        logger.info(f"Claude Vision response: {response_text[:200]}...")
        
        # Strip markdown code blocks if present (```json ... ```)
        if response_text.startswith("```"):
            # Remove opening ```json or ```
            response_text = response_text.split("\n", 1)[1] if "\n" in response_text else response_text[3:]
            # Remove closing ```
            if response_text.endswith("```"):
                response_text = response_text.rsplit("```", 1)[0]
            response_text = response_text.strip()
        
        # Parse JSON response
        collectibles_data = json.loads(response_text)
        collectibles_list = collectibles_data.get("collectibles", [])
        
        logger.info(f"Identified {len(collectibles_list)} collectibles:")
        for i, item in enumerate(collectibles_list):
            logger.info(f"  {i+1}. {item['name']}: {item['description']}")
        
        return collectibles_list
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude Vision response as JSON: {e}")
        logger.error(f"Response was: {response_text}")
        # Return empty list as fallback
        return []
    except Exception as e:
        logger.error(f"Error analyzing collectible metadata: {e}")
        return []


def segment_collectible_sprites(collectible_path: Path, sprite_analyzer, expected_count: int = None) -> List[str]:
    """
    Segment collectible sprite sheet into individual sprites using the same method as character sprites.
    
    Uses SpriteSheetAnalyzer to:
    1. Analyze layout with Claude Vision
    2. Remove background
    3. Extract frames using connected component analysis
    4. Return individual sprite images as base64 data URLs
    
    Args:
        collectible_path: Path to collectible sprite sheet image
        sprite_analyzer: SpriteSheetAnalyzer instance
        
    Returns:
        List of base64 data URLs for individual collectible sprites
    """
    from PIL import Image
    import base64
    import io
    from sprite_processing.background_remover import BackgroundRemover
    
    logger.info(f"Segmenting collectible sprites from: {collectible_path}")
    
    # STEP 1: Always analyze sprite sheet layout using Claude Vision
    # (Don't assume horizontal layout even if we have expected_count - grids are common!)
    logger.info("  Analyzing collectible layout with Claude Vision...")
    layout_info = sprite_analyzer.analyze_sprite_sheet_layout(collectible_path)
    logger.info(f"  Layout: {layout_info['layout_type']} ({layout_info['rows']}×{layout_info['columns']})")
    logger.info(f"  Total collectibles detected: {layout_info['total_frames']}")
    
    # Validate against expected count if provided
    if expected_count and layout_info['total_frames'] != expected_count:
        logger.warning(
            f"  Layout detection found {layout_info['total_frames']} items, "
            f"but metadata analysis found {expected_count} items. Using detected layout."
        )
    
    # STEP 2: Remove background (assume white background)
    logger.info("  Removing background from collectible sheet...")
    original_img = Image.open(collectible_path)
    if original_img.mode != 'RGBA':
        original_img = original_img.convert('RGBA')
    
    bg_remover = BackgroundRemover()
    cleaned_img = bg_remover.remove_background(
        original_img,
        background_color=(255, 255, 255),  # White background
        tolerance=40
    )
    
    # Auto-crop to remove excess transparent space
    cleaned_img = bg_remover.auto_crop(cleaned_img, padding=5)
    logger.info(f"  Background removed: {cleaned_img.size[0]}x{cleaned_img.size[1]}px")
    
    # STEP 3: Extract frames using smart extraction (connected component analysis)
    logger.info("  Extracting individual collectible sprites...")
    
    # Save cleaned image temporarily for extraction
    temp_cleaned_path = collectible_path.parent / f"cleaned_{collectible_path.name}"
    cleaned_img.save(temp_cleaned_path)
    
    # Use the same smart extraction method as character sprites
    frames, frame_width, frame_height = sprite_analyzer.extract_frames_smart(
        temp_cleaned_path,
        rows=layout_info['rows'],
        columns=layout_info['columns']
    )
    
    logger.info(f"  Extracted {len(frames)} collectible sprites at {frame_width}x{frame_height}px each")
    
    # Clean up temp file
    if temp_cleaned_path.exists():
        temp_cleaned_path.unlink()
    
    # STEP 4: Convert each frame to base64 data URL
    sprite_data_urls = []
    for i, frame in enumerate(frames):
        buffer = io.BytesIO()
        frame.save(buffer, format='PNG')
        sprite_data_url = f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode()}"
        sprite_data_urls.append(sprite_data_url)
        logger.info(f"    Collectible {i+1}/{len(frames)}: {frame.size[0]}x{frame.size[1]}px")
    
    return sprite_data_urls


def generate_collectible_positions(
    platforms: List[dict],
    num_collectibles: int = 10,
    min_spacing: int = 80
) -> List[dict]:
    """
    Generate random positions on top of platforms for collectibles.
    
    Args:
        platforms: List of platform dictionaries with x, y, width, height
        num_collectibles: Number of collectibles to place
        min_spacing: Minimum spacing between collectibles
        
    Returns:
        List of collectible position dicts with x, y, sprite_index
    """
    import random
    
    collectible_positions = []
    placed_positions = []
    
    # Try to place collectibles on platforms
    attempts = 0
    max_attempts = num_collectibles * 10
    
    while len(collectible_positions) < num_collectibles and attempts < max_attempts:
        attempts += 1
        
        # Pick a random platform
        platform = random.choice(platforms)
        
        # Generate random x position on platform (with margin)
        margin = 30
        if platform['width'] < margin * 2:
            continue
            
        x = random.randint(
            platform['x'] + margin,
            platform['x'] + platform['width'] - margin
        )
        
        # Position collectible above platform
        y = platform['y'] - 20  # 20px above platform
        
        # Check spacing from other collectibles
        too_close = False
        for placed_x, placed_y in placed_positions:
            distance = ((x - placed_x) ** 2 + (y - placed_y) ** 2) ** 0.5
            if distance < min_spacing:
                too_close = True
                break
        
        if not too_close:
            collectible_positions.append({
                'x': x,
                'y': y,
                'sprite_index': random.randint(0, 10)  # Will be clamped to actual sprite count
            })
            placed_positions.append((x, y))
    
    logger.info(f"Generated {len(collectible_positions)} collectible positions")
    return collectible_positions


def generate_platform_debug(
    background_path: Path,
    platforms: List[dict],
    gaps: List[dict],
    spawn_point: dict
) -> str:
    """
    Generate a debug visualization showing platforms overlaid on the background.

    Args:
        background_path: Path to background image
        platforms: List of platform dictionaries with x, y, width, height
        gaps: List of gap dictionaries
        spawn_point: Spawn point with x, y coordinates

    Returns:
        Base64 encoded PNG image
    """
    from PIL import Image, ImageDraw
    import base64
    import io

    # Load background
    bg_img = Image.open(background_path).convert('RGBA')

    # Create overlay
    overlay = Image.new('RGBA', bg_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Draw platforms (semi-transparent green rectangles)
    for platform in platforms:
        x, y, w, h = platform['x'], platform['y'], platform['width'], platform['height']
        # Filled rectangle with transparency
        draw.rectangle(
            [x, y, x + w, y + h],
            fill=(0, 255, 0, 80),  # Green with alpha
            outline=(0, 255, 0, 255),  # Solid green outline
            width=2
        )
        # Add platform label
        label = f"P: {w}x{h}"
        draw.text((x + 5, y + 5), label, fill=(255, 255, 255, 255))

    # Draw gaps (semi-transparent red rectangles)
    for gap in gaps:
        x, y, w, h = gap.get('x', 0), gap.get('y', 0), gap.get('width', 0), gap.get('height', 0)
        if w > 0 and h > 0:
            draw.rectangle(
                [x, y, x + w, y + h],
                fill=(255, 0, 0, 80),  # Red with alpha
                outline=(255, 0, 0, 255),  # Solid red outline
                width=2
            )
            # Add gap label
            label = f"Gap: {w}px"
            draw.text((x + 5, y + 5), label, fill=(255, 255, 255, 255))

    # Draw spawn point (yellow circle)
    spawn_x, spawn_y = spawn_point['x'], spawn_point['y']
    spawn_radius = 10
    draw.ellipse(
        [spawn_x - spawn_radius, spawn_y - spawn_radius,
         spawn_x + spawn_radius, spawn_y + spawn_radius],
        fill=(255, 255, 0, 200),  # Yellow with alpha
        outline=(255, 255, 0, 255),  # Solid yellow outline
        width=2
    )
    # Add spawn label
    draw.text((spawn_x + 15, spawn_y - 10), "SPAWN", fill=(255, 255, 0, 255))

    # Composite overlay onto background
    result = Image.alpha_composite(bg_img, overlay)

    # Add legend
    legend_draw = ImageDraw.Draw(result)
    legend_y = 10
    legend_draw.rectangle([10, legend_y, 200, legend_y + 80], fill=(0, 0, 0, 180), outline=(255, 255, 255, 255))
    legend_draw.text((15, legend_y + 5), "Platform Debug Legend:", fill=(255, 255, 255, 255))
    legend_draw.rectangle([15, legend_y + 25, 30, legend_y + 35], fill=(0, 255, 0, 80), outline=(0, 255, 0, 255))
    legend_draw.text((35, legend_y + 23), "Walkable Platform", fill=(255, 255, 255, 255))
    legend_draw.rectangle([15, legend_y + 45, 30, legend_y + 55], fill=(255, 0, 0, 80), outline=(255, 0, 0, 255))
    legend_draw.text((35, legend_y + 43), "Gap (must jump)", fill=(255, 255, 255, 255))
    legend_draw.ellipse([15, legend_y + 65, 25, legend_y + 75], fill=(255, 255, 0, 200), outline=(255, 255, 0, 255))
    legend_draw.text((35, legend_y + 63), "Spawn Point", fill=(255, 255, 255, 255))

    # Convert to base64
    buffer = io.BytesIO()
    result.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    return f"data:image/png;base64,{img_base64}"


@app.get("/")
async def root():
    return {"message": "AI Asset Generator API is running", "version": "1.0.0"}


@app.post("/generate-asset-prompts", response_model=PromptResponse, status_code=status.HTTP_200_OK)
async def generate_asset_prompts(request: PromptRequest):
    """
    Generate detailed image generation prompts for game assets (characters, environments, NPCs, backgrounds)
    using Claude 4.5 Sonnet. Results are cached to save time on repeated requests.
    """
    request_id = f"req_{os.urandom(4).hex()}"  # Simple request tracing
    logger.info(f"[{request_id}] Received request: {request.prompt[:100]}...")

    # Check cache first
    cached_result = cache.get(request.prompt)
    if cached_result:
        logger.info(f"[{request_id}] Cache hit! Returning cached result")
        return PromptResponse(result=cached_result, cached=True)

    logger.info(f"[{request_id}] Cache miss. Calling Claude API...")

    try:
        claude_prompt = f"""You are a professional game artist assistant. Based on the following video game description, generate a theme and character sprite prompt.

        Game Description:
        \"{request.prompt}\"

        Return your response as a valid JSON object (no markdown, no ```json blocks, no extra text) with this exact structure:

        {{
        "theme": "A concise theme description (e.g., 'space adventure', 'medieval fantasy', 'cyberpunk city')",
        "main_character": {{
            "prompt": "2D sprite sheet of [CHARACTER] wearing [OUTFIT/GEAR], pixel art style for platformer game. Eight frames of walking animation cycle displayed side by side from left to right. Each frame should be facing to the right. Frame 1: neutral standing pose. Frame 2: left front leg lifting. Frame 3: left front leg fully lifted mid-step. Frame 4: left front leg descending, right front leg preparing. Frame 5: both front legs planted transition. Frame 6: right front leg lifting. Frame 7: right front leg fully lifted mid-step. Frame 8: right front leg descending, completing full walk cycle. Consistent character design across all frames with clear distinct poses. Clean white background, retro game sprite aesthetic, sharp pixel details, [COLOR AND VISUAL DETAILS]",
            "style": "pixel art sprite sheet, 2D platformer game graphics, retro gaming aesthetic",
            "additional_instructions": "Ensure perfect consistency in character design across all eight frames. Each frame should show clear progression of complete walking cycle with distinct leg positions. Frames arranged horizontally in sequence. Clean separation between frames. Wide horizontal composition to fit all 8 frames."
        }}
        }}

        Rules:
        - Output ONLY the raw JSON. No explanations, no markdown, no trailing text.
        - Include a "theme" field with a concise theme description.
        - Include ONLY the "main_character" field with ONE character sprite prompt.
        - For main_character: MUST include detailed 8-frame walking animation cycle description.
        - Replace bracketed placeholders with theme-appropriate content based on the game description.
        - Be creative and detailed with character design.
        - Use double quotes for all JSON keys and strings."""

        logger.info(f"[{request_id}] Calling Claude 4.5 Sonnet...")

        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4096,
            temperature=0.7,
            messages=[{"role": "user", "content": claude_prompt}]
        )

        # Safely extract text content
        if not message.content or len(message.content) == 0:
            raise ValueError("Claude returned no content")

        if not hasattr(message.content[0], "text"):
            raise ValueError(f"Unexpected content type from Claude: {type(message.content[0])}")

        response_text = message.content[0].text.strip()

        if not response_text:
            raise ValueError("Claude returned empty text response")

        logger.success(f"[{request_id}] Successfully generated asset prompts ({len(response_text)} chars)")

        # Auto-detect and remove markdown code fences if present
        if response_text.startswith("```"):
            logger.info(f"[{request_id}] Detected markdown code fences, removing...")
            # Remove ```json or ``` at start and ``` at end
            lines = response_text.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]  # Remove first line with ```json
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]  # Remove last line with ```
            response_text = '\n'.join(lines).strip()
            logger.info(f"[{request_id}] Code fences removed")

        # Parse the Claude response
        try:
            claude_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"[{request_id}] Failed to parse Claude JSON response: {str(e)}")
            logger.error(f"[{request_id}] Response text: {response_text}")
            raise ValueError(f"Invalid JSON from Claude: {str(e)}")

        # Extract theme and main character
        theme = claude_data.get("theme", "")
        main_character = claude_data.get("main_character", {})

        # Create background and collectible prompts with theme interpolation
        background_prompt = {
            "prompt": f"Generate a 2d platformer background with the following {theme}, 8-bit graphics",
            "image_size": "landscape_4_3",
            "output_format": "png"
        }

        collectible_prompt = {
            "prompt": f"Create a sprite sheet of collectible items in the style of an 8-bit retro video game with a white background with the following {theme}",
            "style": "8-bit retro pixel art",
            "output_format": "png"
        }

        # Build final response structure
        final_response = {
            "theme": theme,
            "main_character": {
                "description": f"Main character for {theme}",
                "variations": [main_character]
            },
            "background": {
                "description": f"Background for {theme}",
                "variations": [background_prompt]
            },
            "collectible_item": {
                "description": f"Collectible items for {theme}",
                "variations": [collectible_prompt]
            }
        }

        # Convert back to JSON string for caching and response
        final_json = json.dumps(final_response, indent=2)

        # Cache the result
        cache.set(request.prompt, final_json)
        logger.info(f"[{request_id}] Result cached for future requests")

        return PromptResponse(result=final_json, cached=False)

    # === Specific Anthropic Errors ===
    except AuthenticationError as e:
        error_msg = "Invalid or missing Anthropic API key"
        logger.error(f"[{request_id}] Authentication failed: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg
        ) from e

    except RateLimitError as e:
        error_msg = "Claude API rate limit exceeded. Please try again later."
        logger.warning(f"[{request_id}] Rate limited: {e}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_msg
        ) from e

    except APIStatusError as e:
        error_msg = f"Claude API error {e.status_code}: {e.message}"
        logger.error(f"[{request_id}] API error: {error_msg} | Request ID: {getattr(e, 'request_id', 'N/A')}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error_msg
        ) from e

    except APIConnectionError as e:
        error_msg = "Failed to connect to Claude API (network/DNS/timeout)"
        logger.error(f"[{request_id}] Connection error: {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_msg
        ) from e

    # === Validation / Parsing Errors ===
    except ValueError as e:
        error_msg = f"Invalid response from Claude: {str(e)}"
        logger.error(f"[{request_id}] {error_msg}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=error_msg
        ) from e

    # === Unexpected Errors ===
    except Exception as e:
        tb = traceback.format_exc()
        error_msg = "Unexpected error generating asset prompts"
        logger.exception(f"[{request_id}] {error_msg}: {str(e)}\n{tb}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Check server logs for details."
        ) from e


@app.get("/cached-prompts", response_model=CachedPromptsResponse, status_code=status.HTTP_200_OK)
async def get_cached_prompts():
    """
    Get list of all cached prompts with metadata (timestamp, preview).
    This endpoint is called on frontend load to show previously generated prompts.
    """
    try:
        prompts = cache.get_all_prompts()
        logger.info(f"Retrieved {len(prompts)} cached prompts")
        return CachedPromptsResponse(prompts=prompts, count=len(prompts))
    except Exception as e:
        logger.error(f"Error retrieving cached prompts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cached prompts"
        ) from e


@app.post("/fetch-cached-prompt", response_model=CachedResultResponse, status_code=status.HTTP_200_OK)
async def fetch_cached_prompt(request: FetchCachedRequest):
    """
    Fetch the full generated result for a specific cached prompt.
    Returns the complete asset generation data for the given prompt.
    """
    try:
        cached_data = cache.get_cached_result(request.prompt)
        
        if not cached_data:
            logger.warning(f"Cached prompt not found: {request.prompt[:100]}...")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cached prompt not found"
            )
        
        logger.info(f"Retrieved cached result for prompt: {request.prompt[:100]}...")
        return CachedResultResponse(**cached_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching cached prompt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch cached prompt"
        ) from e


@app.delete("/cache/{prompt}")
async def delete_cached_prompt(prompt: str):
    """
    Delete a specific cached prompt.
    """
    try:
        success = cache.delete(prompt)
        if success:
            logger.info(f"Deleted cached prompt: {prompt[:100]}...")
            return {"message": "Cached prompt deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cached prompt not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting cached prompt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete cached prompt"
        ) from e


@app.delete("/cache")
async def clear_cache():
    """
    Clear all cached prompts.
    """
    try:
        cache.clear()
        logger.info("Cache cleared successfully")
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        ) from e


@app.delete("/image-cache")
async def clear_image_cache():
    """
    Clear all cached images.
    """
    try:
        image_cache.clear()
        logger.info("Image cache cleared successfully")
        return {"message": "Image cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing image cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear image cache"
        ) from e


@app.post("/generate-image-asset", response_model=GenerateImageResponse, status_code=status.HTTP_200_OK)
async def generate_image_asset(request: GenerateImageRequest):
    """
    Generate an image asset from a prompt. 
    Checks cache first and returns cached image URL if available (unless force_regenerate is True).
    """
    request_id = f"img_{os.urandom(4).hex()}"
    logger.info(f"[{request_id}] Image generation request for category: {request.category}")
    logger.info(f"[{request_id}] Prompt: {request.prompt[:100]}...")
    
    if request.force_regenerate:
        logger.info(f"[{request_id}] Force regenerate flag set, bypassing cache")
    else:
        # Check cache first (only if not forcing regeneration)
        cached_url = image_cache.get(
            prompt=request.prompt,
            category=request.category,
            style=request.style,
            additional_instructions=request.additional_instructions,
            image_size=request.image_size,
            output_format=request.output_format
        )
        
        if cached_url:
            logger.info(f"[{request_id}] Returning cached image URL")
            return GenerateImageResponse(
                image_url=cached_url,
                prompt=request.prompt,
                category=request.category,
                cached=True
            )

    # Generate new image
    logger.info(f"[{request_id}] No cache found, generating new image...")
    
    try:
        # Run the blocking image generation in a thread pool
        image_generator_response = await asyncio.to_thread(
            image_generator.generate,
            config=ImageGenerationConfig(
                model_name="fal-ai/alpha-image-232/text-to-image",
                prompt=request.prompt
            )
        )
        
        image_url = image_generator_response['images'][0]['url']
        
        logger.info(f"[{request_id}] Image generated successfully: {image_url}")
        
        # Cache the result
        image_cache.set(
            prompt=request.prompt,
            category=request.category,
            image_url=image_url,
            style=request.style,
            additional_instructions=request.additional_instructions,
            image_size=request.image_size,
            output_format=request.output_format
        )
        
        return GenerateImageResponse(
            image_url=image_url,
            prompt=request.prompt,
            category=request.category,
            cached=False
        )
    
    except Exception as e:
        logger.error(f"[{request_id}] Error generating image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate image: {str(e)}"
        ) from e


@app.post("/generate-game", response_model=GenerateGameResponse, status_code=status.HTTP_200_OK)
async def generate_game(request: GenerateGameRequest):
    """
    Generate a complete playable HTML5 platformer game from asset URLs.

    This endpoint:
    1. Downloads background and character sprite images from provided URLs
    2. Uses Claude Vision API to detect walkable platforms in the background
    3. Processes character sprite (removes background, detects frames)
    4. Generates a complete Phaser.js HTML5 game

    Returns the game HTML and configuration details.
    """
    request_id = f"game_{os.urandom(4).hex()}"
    logger.info(f"[{request_id}] Game generation request")
    logger.info(f"[{request_id}] Background URL: {request.background_url}")
    logger.info(f"[{request_id}] Character URL: {request.character_url}")
    logger.info(f"[{request_id}] Frames: {request.num_frames}, Name: {request.game_name}")

    # Create temporary directory for downloads and generation
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        try:
            # Download background image for analysis
            logger.info(f"[{request_id}] Downloading background image for analysis...")
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                bg_response = await http_client.get(request.background_url)
                bg_response.raise_for_status()

                bg_path = temp_path / "background.png"
                bg_path.write_bytes(bg_response.content)
                logger.info(f"[{request_id}] Background downloaded: {len(bg_response.content)} bytes")

            # Download character sprite for processing
            logger.info(f"[{request_id}] Downloading character sprite for processing...")
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                char_response = await http_client.get(request.character_url)
                char_response.raise_for_status()

                char_path = temp_path / "character.png"
                char_path.write_bytes(char_response.content)
                logger.info(f"[{request_id}] Character sprite downloaded: {len(char_response.content)} bytes")

            # Initialize game generator (need it for sprite_analyzer)
            output_dir = temp_path / "generated_game"
            game_gen = GameGenerator(output_dir=str(output_dir))

            # Download and process collectibles if provided
            collectible_sprites = []
            collectible_positions = []
            collectible_metadata = []
            if request.collectible_url:
                logger.info(f"[{request_id}] Downloading collectible sprite sheet...")
                async with httpx.AsyncClient(timeout=30.0) as http_client:
                    coll_response = await http_client.get(request.collectible_url)
                    coll_response.raise_for_status()

                    coll_path = temp_path / "collectibles.png"
                    coll_path.write_bytes(coll_response.content)
                    logger.info(f"[{request_id}] Collectibles downloaded: {len(coll_response.content)} bytes")

                # Step 1: Analyze collectible metadata with Claude Vision
                logger.info(f"[{request_id}] Analyzing collectible metadata with Claude Vision...")
                collectible_metadata = await asyncio.to_thread(
                    analyze_collectible_metadata,
                    coll_path,
                    client  # Global Anthropic client (not http_client)
                )
                logger.info(f"[{request_id}] Identified {len(collectible_metadata)} collectibles with metadata")

                # Step 2: Segment collectible sprites using the same analyzer as character sprites
                logger.info(f"[{request_id}] Segmenting collectible sprites...")
                collectible_sprites = await asyncio.to_thread(
                    segment_collectible_sprites,
                    coll_path,
                    game_gen.sprite_analyzer,  # Pass the sprite analyzer
                    len(collectible_metadata)  # Pass expected count from metadata
                )
                logger.info(f"[{request_id}] Segmented {len(collectible_sprites)} collectible sprites")
                
                # Verify counts match (metadata should match sprite count)
                if len(collectible_metadata) != len(collectible_sprites):
                    logger.warning(
                        f"[{request_id}] Mismatch: {len(collectible_metadata)} metadata items vs "
                        f"{len(collectible_sprites)} sprites. Some collectibles may not have descriptions."
                    )
                    # Pad metadata with generic entries if needed
                    while len(collectible_metadata) < len(collectible_sprites):
                        idx = len(collectible_metadata)
                        collectible_metadata.append({
                            "name": f"Mystery Item {idx + 1}",
                            "status_effect": "Unknown Effect",
                            "description": "A mysterious collectible item with unknown powers!"
                        })

            # Generate game with URLs (runs in thread pool since it's blocking)
            logger.info(f"[{request_id}] Generating game with Claude Vision analysis...")
            game_html, scene_config, debug_frames = await asyncio.to_thread(
                game_gen.generate_game_html_with_urls,
                character_sprite_path=str(char_path),
                character_sprite_url=request.character_url,
                background_image_path=str(bg_path),
                background_image_url=request.background_url,
                num_frames=request.num_frames,
                game_name=request.game_name,
                collectible_sprites=[],  # Will be updated below if collectibles exist
                collectible_positions=[],  # Will be updated below if collectibles exist
                collectible_metadata=[]  # Will be updated below if collectibles exist
            )
            
            # Generate collectible positions on platforms and regenerate HTML
            if collectible_sprites and len(collectible_sprites) > 0:
                logger.info(f"[{request_id}] Generating collectible positions on platforms...")
                collectible_positions = generate_collectible_positions(
                    platforms=scene_config["physics"]["platforms"],
                    num_collectibles=min(15, len(scene_config["physics"]["platforms"]) * 2)
                )
                # Clamp sprite indices to actual sprite count
                for pos in collectible_positions:
                    pos['sprite_index'] = pos['sprite_index'] % len(collectible_sprites)
                
                # Regenerate HTML with collectibles and metadata
                logger.info(f"[{request_id}] Regenerating game HTML with collectibles...")
                game_html = game_gen.web_exporter._generate_html(
                    scene_config,
                    request.background_url,
                    scene_config['character']['sprite_path'],
                    collectible_sprites,
                    collectible_positions,
                    collectible_metadata
                )

            logger.info(f"[{request_id}] Game HTML generated: {len(game_html)} characters")
            logger.info(f"[{request_id}] Debug frames extracted: {len(debug_frames)}")

            # Extract statistics
            platforms_detected = len(scene_config["physics"]["platforms"])
            gaps_detected = len(scene_config["analysis"].get("gaps", []))
            spawn_point = scene_config["analysis"]["spawn"]

            # Generate platform debug visualization if requested
            debug_platforms = ""
            if request.debug_options.get("show_platforms", False):
                logger.info(f"[{request_id}] Generating platform debug visualization...")
                debug_platforms = await asyncio.to_thread(
                    generate_platform_debug,
                    bg_path,
                    scene_config["physics"]["platforms"],
                    scene_config["analysis"].get("gaps", []),
                    spawn_point
                )
                logger.info(f"[{request_id}] Platform debug visualization generated")

            logger.success(f"[{request_id}] Game generated successfully!")
            logger.info(f"[{request_id}] Platforms: {platforms_detected}, Gaps: {gaps_detected}")

            # Prepare debug collectibles data (combine sprites with metadata)
            debug_collectibles_data = []
            if collectible_sprites and collectible_metadata:
                for i, sprite_data_url in enumerate(collectible_sprites):
                    metadata = collectible_metadata[i] if i < len(collectible_metadata) else {
                        "name": f"Mystery Item {i + 1}",
                        "status_effect": "Unknown Effect",
                        "description": "A mysterious collectible item!"
                    }
                    debug_collectibles_data.append({
                        "sprite": sprite_data_url,
                        "name": metadata.get("name", "Unknown"),
                        "status_effect": metadata.get("status_effect", "Unknown Effect"),
                        "description": metadata.get("description", "")
                    })
            
            return GenerateGameResponse(
                game_html=game_html,
                scene_config=scene_config,
                platforms_detected=platforms_detected,
                gaps_detected=gaps_detected,
                spawn_point=spawn_point,
                debug_frames=debug_frames if request.debug_options.get("show_sprite_frames", True) else [],
                debug_platforms=debug_platforms,
                debug_collectibles=debug_collectibles_data if request.debug_options.get("show_collectibles", True) else []
            )

        except httpx.HTTPStatusError as e:
            error_msg = f"Failed to download image: {e.response.status_code} {e.response.reason_phrase}"
            logger.error(f"[{request_id}] {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            ) from e

        except httpx.RequestError as e:
            error_msg = f"Network error downloading image: {str(e)}"
            logger.error(f"[{request_id}] {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=error_msg
            ) from e

        except ValueError as e:
            # GameGenerator raises ValueError for missing API key
            error_msg = str(e)
            logger.error(f"[{request_id}] Configuration error: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Server configuration error: {error_msg}"
            ) from e

        except Exception as e:
            error_msg = f"Failed to generate game: {str(e)}"
            logger.exception(f"[{request_id}] {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            ) from e


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting AI Asset Generator API on http://0.0.0.0:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)