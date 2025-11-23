import { useNavigate } from 'react-router-dom'
import { useAssetContext } from '../context/AssetContext'
import { useEffect } from 'react'

const GameSandbox = () => {
  const navigate = useNavigate()
  const { generatedImages } = useAssetContext()

  useEffect(() => {
    // Redirect if no images are available
    if (!generatedImages.background && !generatedImages.mainCharacter && !generatedImages.collectible) {
      navigate('/')
    }
  }, [generatedImages, navigate])

  const handleBack = () => {
    navigate('/generate-assets')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <svg
                className="w-8 h-8 text-green-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <h1 className="text-3xl font-bold text-white">Game Sandbox</h1>
            </div>
            <button
              onClick={handleBack}
              className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-lg transition-colors flex items-center space-x-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              <span>Back to Assets</span>
            </button>
          </div>

          {/* Game Sandbox Container */}
          <div className="relative w-full bg-black rounded-2xl shadow-2xl overflow-hidden border-4 border-white/20">
            {/* Aspect ratio container for game canvas */}
            <div className="relative w-full" style={{ paddingBottom: '75%' }}> {/* 4:3 aspect ratio */}
              
              {/* Background Image */}
              {generatedImages.background && (
                <div className="absolute inset-0">
                  <img
                    src={generatedImages.background}
                    alt="Game Background"
                    className="w-full h-full object-cover"
                  />
                </div>
              )}

              {/* Main Character Sprite - Positioned in lower center */}
              {generatedImages.mainCharacter && (
                <div className="absolute bottom-16 left-1/2 transform -translate-x-1/2 z-10">
                  <img
                    src={generatedImages.mainCharacter}
                    alt="Main Character"
                    className="h-32 w-auto object-contain drop-shadow-2xl"
                    style={{ imageRendering: 'pixelated' }}
                  />
                </div>
              )}

              {/* Collectible Items - Scattered around */}
              {generatedImages.collectible && (
                <>
                  {/* Collectible 1 - Top Left */}
                  <div className="absolute top-12 left-16 z-5">
                    <img
                      src={generatedImages.collectible}
                      alt="Collectible Item"
                      className="h-16 w-auto object-contain drop-shadow-lg animate-bounce"
                      style={{ imageRendering: 'pixelated', animationDuration: '2s' }}
                    />
                  </div>

                  {/* Collectible 2 - Top Right */}
                  <div className="absolute top-20 right-20 z-5">
                    <img
                      src={generatedImages.collectible}
                      alt="Collectible Item"
                      className="h-16 w-auto object-contain drop-shadow-lg animate-bounce"
                      style={{ imageRendering: 'pixelated', animationDuration: '2.5s', animationDelay: '0.5s' }}
                    />
                  </div>

                  {/* Collectible 3 - Middle Left */}
                  <div className="absolute top-1/2 left-24 transform -translate-y-1/2 z-5">
                    <img
                      src={generatedImages.collectible}
                      alt="Collectible Item"
                      className="h-16 w-auto object-contain drop-shadow-lg animate-bounce"
                      style={{ imageRendering: 'pixelated', animationDuration: '3s', animationDelay: '1s' }}
                    />
                  </div>

                  {/* Collectible 4 - Middle Right */}
                  <div className="absolute top-1/2 right-28 transform -translate-y-1/2 z-5">
                    <img
                      src={generatedImages.collectible}
                      alt="Collectible Item"
                      className="h-16 w-auto object-contain drop-shadow-lg animate-bounce"
                      style={{ imageRendering: 'pixelated', animationDuration: '2.2s', animationDelay: '0.3s' }}
                    />
                  </div>
                </>
              )}

              {/* Overlay UI - Game HUD */}
              <div className="absolute top-4 left-4 right-4 flex items-start justify-between z-20">
                <div className="bg-black/60 backdrop-blur-sm px-4 py-2 rounded-lg border border-white/30">
                  <p className="text-white text-sm font-mono">SANDBOX PREVIEW</p>
                </div>
                <div className="bg-black/60 backdrop-blur-sm px-4 py-2 rounded-lg border border-white/30">
                  <p className="text-white text-sm font-mono">Score: 0</p>
                </div>
              </div>

              {/* Bottom Instructions */}
              <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-20">
                <div className="bg-black/60 backdrop-blur-sm px-6 py-3 rounded-lg border border-white/30">
                  <p className="text-white text-xs font-mono text-center">
                    Game assets rendered from your AI-generated prompts
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Asset Info Cards */}
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Main Character Card */}
            {generatedImages.mainCharacter && (
              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/20">
                <h3 className="text-white font-semibold mb-2 flex items-center space-x-2">
                  <span className="text-2xl">🎮</span>
                  <span>Main Character</span>
                </h3>
                <p className="text-purple-200 text-sm">Player sprite with walking animation</p>
              </div>
            )}

            {/* Background Card */}
            {generatedImages.background && (
              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/20">
                <h3 className="text-white font-semibold mb-2 flex items-center space-x-2">
                  <span className="text-2xl">🌍</span>
                  <span>Background</span>
                </h3>
                <p className="text-purple-200 text-sm">Game world environment scene</p>
              </div>
            )}

            {/* Collectible Card */}
            {generatedImages.collectible && (
              <div className="bg-white/10 backdrop-blur-lg rounded-xl p-4 border border-white/20">
                <h3 className="text-white font-semibold mb-2 flex items-center space-x-2">
                  <span className="text-2xl">💎</span>
                  <span>Collectibles</span>
                </h3>
                <p className="text-purple-200 text-sm">Items scattered throughout the level</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default GameSandbox
