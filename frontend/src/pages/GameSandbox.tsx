import { useNavigate } from 'react-router-dom'
import { useAssetContext } from '../context/AssetContext'
import { useEffect, useState } from 'react'

const GameSandbox = () => {
  const navigate = useNavigate()
  const { generatedImages } = useAssetContext()
  const [gameHtml, setGameHtml] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [gameStats, setGameStats] = useState<{
    platforms_detected: number
    gaps_detected: number
    spawn_point: { x: number; y: number }
  } | null>(null)

  useEffect(() => {
    // Redirect if no images are available
    if (!generatedImages.background || !generatedImages.mainCharacter) {
      navigate('/')
      return
    }

    // Generate game from assets
    generateGame()
  }, [generatedImages, navigate])

  const generateGame = async () => {
    setLoading(true)
    setError('')

    try {
      const response = await fetch('http://localhost:8000/generate-game', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          background_url: generatedImages.background,
          character_url: generatedImages.mainCharacter,
          num_frames: 8,
          game_name: 'AIGeneratedPlatformer',
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to generate game')
      }

      const data = await response.json()
      setGameHtml(data.game_html)
      setGameStats({
        platforms_detected: data.platforms_detected,
        gaps_detected: data.gaps_detected,
        spawn_point: data.spawn_point,
      })
    } catch (err) {
      console.error('Error generating game:', err)
      setError(err instanceof Error ? err.message : 'Failed to generate game')
    } finally {
      setLoading(false)
    }
  }

  const handleBack = () => {
    navigate('/generate-assets')
  }

  const handleRegenerate = () => {
    generateGame()
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
              {loading && (
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span className="text-purple-200 text-sm">Generating game with AI...</span>
                </div>
              )}
            </div>
            <div className="flex items-center space-x-3">
              {!loading && gameHtml && (
                <button
                  onClick={handleRegenerate}
                  className="px-4 py-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 rounded-lg transition-colors flex items-center space-x-2 border border-green-500/30"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  <span>Regenerate</span>
                </button>
              )}
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
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 bg-red-500/10 border border-red-500/30 rounded-xl p-4">
              <div className="flex items-start space-x-3">
                <svg
                  className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <div>
                  <h3 className="text-red-400 font-semibold mb-1">Generation Failed</h3>
                  <p className="text-red-200 text-sm">{error}</p>
                  <button
                    onClick={handleRegenerate}
                    className="mt-3 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors text-sm"
                  >
                    Try Again
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Game Container */}
          <div className="relative w-full bg-black rounded-2xl shadow-2xl overflow-hidden border-4 border-white/20">
            {loading ? (
              // Loading State
              <div
                className="relative w-full flex items-center justify-center bg-gradient-to-br from-purple-900/50 to-slate-900/50"
                style={{ paddingBottom: '75%' }}
              >
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-green-400 mb-4"></div>
                  <p className="text-white text-lg font-semibold mb-2">Generating Your Game...</p>
                  <p className="text-purple-200 text-sm max-w-md text-center px-4">
                    Claude AI is analyzing your assets and creating a playable platformer with physics, platforms,
                    and animations
                  </p>
                  <div className="mt-6 flex items-center space-x-4 text-purple-300 text-xs">
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                      <span>Processing sprites</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                      <span>Detecting platforms</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                      <span>Building game</span>
                    </div>
                  </div>
                </div>
              </div>
            ) : gameHtml ? (
              // Game iframe
              <div className="relative w-full" style={{ paddingBottom: '75%' }}>
                <iframe
                  srcDoc={gameHtml}
                  className="absolute inset-0 w-full h-full border-0"
                  title="Generated Game"
                  sandbox="allow-scripts allow-same-origin"
                />
              </div>
            ) : null}
          </div>

          {/* Game Stats */}
          {gameStats && !loading && (
            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 backdrop-blur-lg rounded-xl p-4 border border-green-500/30">
                <h3 className="text-green-400 font-semibold mb-2 flex items-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <span>Platforms Detected</span>
                </h3>
                <p className="text-white text-3xl font-bold">{gameStats.platforms_detected}</p>
                <p className="text-green-200 text-xs mt-1">AI-detected walkable surfaces</p>
              </div>

              <div className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 backdrop-blur-lg rounded-xl p-4 border border-purple-500/30">
                <h3 className="text-purple-400 font-semibold mb-2 flex items-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 10V3L4 14h7v7l9-11h-7z"
                    />
                  </svg>
                  <span>Gaps to Jump</span>
                </h3>
                <p className="text-white text-3xl font-bold">{gameStats.gaps_detected}</p>
                <p className="text-purple-200 text-xs mt-1">Challenge points requiring jumps</p>
              </div>

              <div className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 backdrop-blur-lg rounded-xl p-4 border border-blue-500/30">
                <h3 className="text-blue-400 font-semibold mb-2 flex items-center space-x-2">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                    />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  <span>Spawn Point</span>
                </h3>
                <p className="text-white text-xl font-bold">
                  ({gameStats.spawn_point.x}, {gameStats.spawn_point.y})
                </p>
                <p className="text-blue-200 text-xs mt-1">Starting position coordinates</p>
              </div>
            </div>
          )}

          {/* Controls Info */}
          {gameHtml && !loading && (
            <div className="mt-6 bg-white/5 backdrop-blur-lg rounded-xl p-6 border border-white/10">
              <h3 className="text-white font-semibold mb-4 flex items-center space-x-2">
                <svg className="w-5 h-5 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"
                  />
                </svg>
                <span>Game Controls</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center space-x-3">
                  <div className="bg-white/10 px-3 py-2 rounded font-mono text-white">← →</div>
                  <span className="text-purple-200 text-sm">Move Left/Right</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="bg-white/10 px-3 py-2 rounded font-mono text-white">SPACE</div>
                  <span className="text-purple-200 text-sm">Jump (Double Jump!)</span>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="bg-white/10 px-3 py-2 rounded font-mono text-white">R</div>
                  <span className="text-purple-200 text-sm">Reset Position</span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default GameSandbox
