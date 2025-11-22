# AI Asset Generator Backend

FastAPI backend server that uses Claude API to generate image prompts for video game assets.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the backend directory:
```bash
cp .env.example .env
```

4. Add your Anthropic API key to the `.env` file:
```
ANTHROPIC_API_KEY=your_actual_api_key_here
```

## Running the Server

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### POST /generate-asset-prompts

Generate image generation prompts based on a video game theme.

**Request Body:**
```json
{
  "prompt": "cyberpunk noir detective game"
}
```

**Response:**
```json
{
  "result": "Detailed prompts for main character, environment, NPCs, and backgrounds..."
}
```

