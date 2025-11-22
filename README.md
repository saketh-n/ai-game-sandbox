# AI Video Game Asset Generator & Sandbox

A full-stack application for generating video game assets using AI. Built with React/TypeScript frontend and Python FastAPI backend, powered by Claude AI.

## 🏗️ Project Structure

```
ai-asset-gen-sandbox/
├── frontend/          # React + TypeScript + Tailwind CSS
│   ├── src/
│   ├── package.json
│   └── ...
├── backend/           # Python FastAPI server
│   ├── main.py
│   ├── requirements.txt
│   └── ...
└── README.md
```

## 🚀 Quick Start

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file with your Anthropic API key
echo "ANTHROPIC_API_KEY=your_actual_api_key_here" > .env

# Start the server
uvicorn main:app --reload
```

The backend will run at `http://localhost:8000`

### 2. Frontend Setup

Open a new terminal:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will run at `http://localhost:5173`

## 🎮 How It Works

1. **Enter a theme**: Type a video game theme in the input box (e.g., "cyberpunk noir detective game")
2. **Press Enter**: The frontend sends your theme to the backend
3. **AI Processing**: Backend calls Claude API to generate detailed asset prompts
4. **View Results**: See AI-generated prompts organized by:
   - 🎮 **Main Character** - Multiple variations with detailed descriptions
   - 🌍 **Environment Assets** - Ground tiles, platforms, props, trees, rocks, etc.
   - 👥 **NPCs** - Allies, enemies, and neutral characters
   - 🎨 **Background Scenes** - Full scene compositions for different levels/areas
5. **Edit & Copy**: Each prompt is editable and has a copy button for easy use

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Main Endpoint

**POST** `/generate-asset-prompts`

Request:
```json
{
  "prompt": "cyberpunk noir detective game"
}
```

Response:
```json
{
  "result": "Detailed prompts for game assets..."
}
```

## 🎨 Features

- ✨ **Beautiful UI**: Modern gradient design with glassmorphism effects
- 🤖 **AI-Powered**: Uses Claude Sonnet 4.5 for intelligent prompt generation
- ⚡ **Fast & Responsive**: Built with Vite and FastAPI
- 🔄 **Loading States**: Smooth animations while waiting for AI responses
- ❌ **Error Handling**: Clear error messages if something goes wrong
- 📝 **Type-Safe**: Full TypeScript support on frontend
- 📋 **Structured Output**: Organized, collapsible sections for each asset category
- ✏️ **Editable Prompts**: Modify any generated prompt in real-time
- 📄 **One-Click Copy**: Copy button for each prompt variation
- 🎯 **Comprehensive Assets**: Characters, environments, NPCs, and backgrounds all generated at once

## 🛠️ Tech Stack

### Frontend
- **React 18** - UI library
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **Vite** - Build tool

### Backend
- **Python 3.8+** - Programming language
- **FastAPI** - Web framework
- **Anthropic Claude API** - AI model
- **Uvicorn** - ASGI server

## 🔧 Configuration

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

Get your API key from: https://console.anthropic.com/

### CORS Configuration

The backend is configured to accept requests from:
- `http://localhost:5173` (Vite default)
- `http://localhost:3000` (Alternative port)

## Prompts
The following are prompt templates for generating various assets

### Character
```
{user_instruction}
Generate a character this centered within the image. Make the background white.
The character is well visible within the scene and is well rendered
```

### Background
```
{user_instruction}
Make this background fit the scene and well visible. Focus on making the background be well shown
```

### Item
```
{user_instruction}
Make this item be visible within the center of the image. Make the background white around the item
```

## 📝 License

MIT
