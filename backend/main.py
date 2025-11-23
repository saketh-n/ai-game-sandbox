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
    num_frames: int = Field(default=8, description="Number of animation frames in sprite sheet")
    game_name: str = Field(default="GeneratedGame", description="Name for the generated game")

class GenerateGameResponse(BaseModel):
    game_html: str = Field(..., description="Complete HTML game code")
    scene_config: dict = Field(..., description="Game scene configuration")
    platforms_detected: int = Field(..., description="Number of platforms detected by AI")
    gaps_detected: int = Field(..., description="Number of gaps detected")
    spawn_point: dict = Field(..., description="Character spawn coordinates")
    debug_frames: List[str] = Field(default=[], description="Base64 encoded debug frames for visualization")

image_generator = ImageGenerator(api_key=os.getenv("FAL_KEY"))


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
            "prompt": "2D sprite sheet of [CHARACTER] wearing [OUTFIT/GEAR], pixel art style for platformer game. Eight frames of walking animation cycle displayed side by side from left to right. Frame 1: neutral standing pose. Frame 2: left front leg lifting. Frame 3: left front leg fully lifted mid-step. Frame 4: left front leg descending, right front leg preparing. Frame 5: both front legs planted transition. Frame 6: right front leg lifting. Frame 7: right front leg fully lifted mid-step. Frame 8: right front leg descending, completing full walk cycle. Consistent character design across all frames with clear distinct poses. Clean white background, retro game sprite aesthetic, sharp pixel details, [COLOR AND VISUAL DETAILS]",
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
            async with httpx.AsyncClient(timeout=30.0) as client:
                bg_response = await client.get(request.background_url)
                bg_response.raise_for_status()

                bg_path = temp_path / "background.png"
                bg_path.write_bytes(bg_response.content)
                logger.info(f"[{request_id}] Background downloaded: {len(bg_response.content)} bytes")

            # Download character sprite for processing
            logger.info(f"[{request_id}] Downloading character sprite for processing...")
            async with httpx.AsyncClient(timeout=30.0) as client:
                char_response = await client.get(request.character_url)
                char_response.raise_for_status()

                char_path = temp_path / "character.png"
                char_path.write_bytes(char_response.content)
                logger.info(f"[{request_id}] Character sprite downloaded: {len(char_response.content)} bytes")

            # Initialize game generator
            output_dir = temp_path / "generated_game"
            game_gen = GameGenerator(output_dir=str(output_dir))

            # Generate game with URLs (runs in thread pool since it's blocking)
            logger.info(f"[{request_id}] Generating game with Claude Vision analysis...")
            game_html, scene_config, debug_frames = await asyncio.to_thread(
                game_gen.generate_game_html_with_urls,
                character_sprite_path=str(char_path),
                character_sprite_url=request.character_url,
                background_image_path=str(bg_path),
                background_image_url=request.background_url,
                num_frames=request.num_frames,
                game_name=request.game_name
            )

            logger.info(f"[{request_id}] Game HTML generated: {len(game_html)} characters")
            logger.info(f"[{request_id}] Debug frames extracted: {len(debug_frames)}")

            # Extract statistics
            platforms_detected = len(scene_config["physics"]["platforms"])
            gaps_detected = len(scene_config["analysis"].get("gaps", []))
            spawn_point = scene_config["analysis"]["spawn"]

            logger.success(f"[{request_id}] Game generated successfully!")
            logger.info(f"[{request_id}] Platforms: {platforms_detected}, Gaps: {gaps_detected}")

            return GenerateGameResponse(
                game_html=game_html,
                scene_config=scene_config,
                platforms_detected=platforms_detected,
                gaps_detected=gaps_detected,
                spawn_point=spawn_point,
                debug_frames=debug_frames
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