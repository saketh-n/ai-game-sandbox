from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from anthropic import Anthropic, APIStatusError, APIConnectionError, AuthenticationError, RateLimitError
from loguru import logger
import os
from dotenv import load_dotenv
import traceback

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


@app.get("/")
async def root():
    return {"message": "AI Asset Generator API is running", "version": "1.0.0"}


@app.post("/generate-asset-prompts", response_model=PromptResponse, status_code=status.HTTP_200_OK)
async def generate_asset_prompts(request: PromptRequest):
    """
    Generate detailed image generation prompts for game assets (characters, environments, NPCs, backgrounds)
    using Claude 4.5 Sonnet.
    """
    request_id = f"req_{os.urandom(4).hex()}"  # Simple request tracing
    logger.info(f"[{request_id}] Received request: {request.prompt[:100]}...")

    try:
        claude_prompt = f"""Based on the following video game description, generate high-quality, detailed prompts suitable for image generation models (DALL-E, Midjourney, Stable Diffusion, Flux, etc.).

Game Description:
\"{request.prompt}\"

Please generate prompts for:
1. Main character (hero/protagonist) - multiple variations if applicable
2. Environment assets - first list out what key environmental elements are needed, then provide detailed prompts for each
3. NPCs (non-player characters) - allies, enemies, merchants, etc.
4. Backgrounds / scenes - key locations, menus, loading screens

Make all prompts highly descriptive, include art style suggestions, lighting, mood, composition tips, and specific details that help generate consistent and professional-looking game assets.

Format your response clearly with headings."""

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

        return PromptResponse(result=response_text)

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


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting AI Asset Generator API on http://0.0.0.0:8000")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)