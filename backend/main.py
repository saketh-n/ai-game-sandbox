from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from anthropic import Anthropic, APIStatusError, APIConnectionError, AuthenticationError, RateLimitError
from loguru import logger
import os
from dotenv import load_dotenv
import traceback
from typing import List
import asyncio
from cache_manager import cache

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

class GenerateImageResponse(BaseModel):
    image_url: str
    prompt: str
    category: str


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
        claude_prompt = f"""You are a professional game artist assistant. Based on the following video game description, generate image generation prompts for all required assets.

        Game Description:
        \"{request.prompt}\"

        Return your response as a valid JSON object (no markdown, no ```json blocks, no extra text) with this exact structure:

        {{
        "main_character": {{
            "description": "Brief overall description of the protagonist",
            "variations": [
            "Detailed prompt for variation 1 -- highly descriptive, include art style, lighting, pose, colors, mood, camera angle, etc.",
            "Detailed prompt for variation 2...",
            "..."
            ]
        }},
        "environment_assets": {{
            "key_elements_needed": ["ground tiles", "trees", "rocks", "props", "..."],
            "assets": {{
            "ground_tiles": {{
                "variations": ["prompt 1", "prompt 2", "..."]
            }},
            "trees": {{
                "variations": ["prompt 1", "prompt 2", "..."]
            }},
            "rocks": {{
                "variations": ["prompt 1", "..."]
            }}
            // add more assets as needed
            }}
        }},
        "npcs": {{
            "categories": {{
            "allies": {{
                "variations": ["friendly knight prompt...", "healer prompt...", "..."]
            }},
            "enemies": {{
                "variations": ["goblin warrior...", "dark sorcerer...", "..."]
            }},
            "neutral": {{
                "variations": ["merchant prompt...", "villager prompt...", "..."]
            }}
            }}
        }},
        "backgrounds": {{
            "scenes": [
            "Full scene prompt for main hub / level 1 background -- parallax-ready, atmospheric, detailed",
            "Menu background prompt -- cinematic, moody",
            "Boss arena background prompt...",
            "..."
            ]
        }}
        }}

        Rules:
        - Output ONLY the raw JSON. No explanations, no markdown, no trailing text.
        - Every prompt must be highly detailed and optimized for Stable Diffusion / Flux / Midjourney.
        - Include art style, lighting, composition, color palette, mood, and camera perspective.
        - Use double quotes for all JSON keys and strings.
        - Do not escape newlines inside strings — keep prompts readable.
        - If a section has only one variation, still put it in a list with one item.
        - Be creative and consistent with the game theme."""

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

        # Cache the result
        cache.set(request.prompt, response_text)
        logger.info(f"[{request_id}] Result cached for future requests")

        return PromptResponse(result=response_text, cached=False)

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


@app.post("/generate-image-asset", response_model=GenerateImageResponse, status_code=status.HTTP_200_OK)
async def generate_image_asset(request: GenerateImageRequest):
    """
    Generate an image asset from a prompt. 
    Currently a dummy implementation with 30-second timeout that returns a placeholder image.
    """
    request_id = f"img_{os.urandom(4).hex()}"
    logger.info(f"[{request_id}] Image generation request for category: {request.category}")
    logger.info(f"[{request_id}] Prompt: {request.prompt[:100]}...")
    
    try:
        # Return a placeholder image URL (using picsum.photos for demo)
        # Different seed based on category for variety
        category_seed = abs(hash(request.category)) % 1000
        image_url = f"https://picsum.photos/seed/{category_seed}/512/512"
        
        logger.info(f"[{request_id}] Image generated successfully: {image_url}")
        
        return GenerateImageResponse(
            image_url=image_url,
            prompt=request.prompt,
            category=request.category
        )
    
    except Exception as e:
        logger.error(f"[{request_id}] Error generating image: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate image: {str(e)}"
        ) from e


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting AI Asset Generator API on http://0.0.0.0:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)