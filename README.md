# AI Video Game Asset Generator & Sandbox

A beautiful, modern web application for generating video game assets using AI, with real-time sandboxing capabilities.

## Features

- 🎮 Video game theme input with intuitive UI
- 🎨 Beautiful gradient background with glassmorphism design
- ⚡ Built with React, TypeScript, and Tailwind CSS
- 🚀 Fast development with Vite

## Getting Started

### Prerequisites

- Node.js (v18 or higher recommended)
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser and navigate to `http://localhost:5173`

## Available Scripts

- `npm run dev` - Start the development server
- `npm run build` - Build for production
- `npm run preview` - Preview the production build
- `npm run lint` - Run ESLint

## Tech Stack

- **React** - UI library
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Vite** - Next-generation frontend tooling

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

## License

MIT



