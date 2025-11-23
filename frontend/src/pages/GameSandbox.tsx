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
  const [debugFrames, setDebugFrames] = useState<string[]>([])
  const [debugPlatforms, setDebugPlatforms] = useState<string>('')
  const [debugCollectibles, setDebugCollectibles] = useState<Array<{
    sprite: string
    name: string
    status_effect: string
    description: string
  }>>([])
  const [showDebugFrames, setShowDebugFrames] = useState(false)
  const [showDebugPlatforms, setShowDebugPlatforms] = useState(false)
  const [showDebugCollectibles, setShowDebugCollectibles] = useState(false)
  const [debugOptions, setDebugOptions] = useState({
    show_sprite_frames: true,
    show_platforms: false,
    show_collectibles: true,
  })

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
          mob_url: generatedImages.mob || null,
          collectible_url: generatedImages.collectible || null,
          num_frames: 8,
          game_name: 'AIGeneratedPlatformer',
          debug_options: debugOptions,
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
      setDebugFrames(data.debug_frames || [])
      setDebugPlatforms(data.debug_platforms || '')
      setDebugCollectibles(data.debug_collectibles || [])
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

          {/* Debug Options */}
          {!loading && gameHtml && (
            <div className="mt-6 bg-white/5 backdrop-blur-lg rounded-xl p-4 border border-white/10">
              <h3 className="text-white font-semibold mb-3 flex items-center space-x-2">
                <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                </svg>
                <span>Debug Visualizations</span>
              </h3>
              <div className="flex flex-wrap gap-4">
                <label className="flex items-center space-x-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={debugOptions.show_sprite_frames}
                    onChange={(e) => setDebugOptions({...debugOptions, show_sprite_frames: e.target.checked})}
                    className="w-4 h-4 rounded border-white/30 bg-white/10 text-green-500 focus:ring-green-500 focus:ring-offset-0"
                  />
                  <span className="text-purple-200 group-hover:text-white transition-colors">Show Sprite Frames</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={debugOptions.show_platforms}
                    onChange={(e) => setDebugOptions({...debugOptions, show_platforms: e.target.checked})}
                    className="w-4 h-4 rounded border-white/30 bg-white/10 text-green-500 focus:ring-green-500 focus:ring-offset-0"
                  />
                  <span className="text-purple-200 group-hover:text-white transition-colors">Show Platform Map</span>
                </label>
                <label className="flex items-center space-x-2 cursor-pointer group">
                  <input
                    type="checkbox"
                    checked={debugOptions.show_collectibles}
                    onChange={(e) => setDebugOptions({...debugOptions, show_collectibles: e.target.checked})}
                    className="w-4 h-4 rounded border-white/30 bg-white/10 text-green-500 focus:ring-green-500 focus:ring-offset-0"
                  />
                  <span className="text-purple-200 group-hover:text-white transition-colors">Show Collectibles</span>
                </label>
                <button
                  onClick={handleRegenerate}
                  className="ml-auto px-3 py-1 bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 rounded text-sm transition-colors border border-yellow-500/30"
                >
                  Apply & Regenerate
                </button>
              </div>
            </div>
          )}

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

          {/* Debug: Platform Visualization */}
          {debugPlatforms && !loading && (
            <div className="mt-6 bg-white/5 backdrop-blur-lg rounded-xl border border-white/10 overflow-hidden">
              <button
                onClick={() => setShowDebugPlatforms(!showDebugPlatforms)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <svg className="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
                  </svg>
                  <span className="text-white font-semibold">Debug: Platform & Collision Map</span>
                </div>
                <svg className={`w-5 h-5 text-white transition-transform ${showDebugPlatforms ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {showDebugPlatforms && (
                <div className="p-6 border-t border-white/10">
                  <p className="text-purple-200 text-sm mb-4">
                    This visualization shows the walkable platforms (green), gaps requiring jumps (red), and the character spawn point (yellow) detected by Claude Vision AI.
                  </p>
                  <div className="bg-black rounded-lg border-2 border-white/20 overflow-hidden">
                    <img
                      src={debugPlatforms}
                      alt="Platform Debug Visualization"
                      className="w-full h-auto"
                    />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Debug: Sprite Frames */}
          {debugFrames.length > 0 && !loading && (
            <div className="mt-6 bg-white/5 backdrop-blur-lg rounded-xl border border-white/10 overflow-hidden">
              <button
                onClick={() => setShowDebugFrames(!showDebugFrames)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <svg
                    className="w-5 h-5 text-yellow-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  <span className="text-white font-semibold">Debug: Extracted Sprite Frames ({debugFrames.length})</span>
                </div>
                <svg
                  className={`w-5 h-5 text-white transition-transform ${showDebugFrames ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {showDebugFrames && (
                <div className="p-6 border-t border-white/10">
                  <p className="text-purple-200 text-sm mb-4">
                    These are the individual frames extracted from the sprite sheet after grid detection and rearrangement.
                    Each frame should show the character in a consistent position without cut-offs.
                  </p>
                  <div className="grid grid-cols-4 md:grid-cols-8 gap-4">
                    {debugFrames.map((frame, index) => (
                      <div key={index} className="relative group">
                        <div className="bg-white/10 rounded-lg p-2 border border-white/20 hover:border-yellow-400 transition-colors">
                          <img
                            src={frame}
                            alt={`Frame ${index}`}
                            className="w-full h-auto"
                            style={{ imageRendering: 'pixelated' }}
                          />
                        </div>
                        <div className="absolute -top-2 -right-2 bg-yellow-400 text-black text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center">
                          {index}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Debug: Collectible Sprites */}
          {debugCollectibles.length > 0 && !loading && (
            <div className="mt-6 bg-white/5 backdrop-blur-lg rounded-xl border border-white/10 overflow-hidden">
              <button
                onClick={() => setShowDebugCollectibles(!showDebugCollectibles)}
                className="w-full px-6 py-4 flex items-center justify-between hover:bg-white/5 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <svg
                    className="w-5 h-5 text-amber-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <span className="text-white font-semibold">Debug: Extracted Collectible Sprites ({debugCollectibles.length})</span>
                </div>
                <svg
                  className={`w-5 h-5 text-white transition-transform ${showDebugCollectibles ? 'rotate-180' : ''}`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>

              {showDebugCollectibles && (
                <div className="p-6 border-t border-white/10">
                  <p className="text-purple-200 text-sm mb-4">
                    These are the individual collectible items extracted from the collectible sprite sheet.
                    Each item shows its sprite, name, status effect, and description as analyzed by Claude AI.
                  </p>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                    {debugCollectibles.map((collectible, index) => (
                      <div key={index} className="relative group">
                        <div className="bg-gradient-to-br from-white/10 to-white/5 rounded-lg p-4 border border-white/20 hover:border-amber-400 transition-all hover:scale-105">
                          <div className="bg-black/30 rounded-lg p-3 mb-3 flex items-center justify-center" style={{ minHeight: '100px' }}>
                            <img
                              src={collectible.sprite}
                              alt={collectible.name}
                              className="max-w-full max-h-24 object-contain"
                              style={{ imageRendering: 'pixelated' }}
                            />
                          </div>
                          <div className="text-center">
                            <h4 className="text-white font-semibold text-sm mb-1 truncate" title={collectible.name}>
                              {collectible.name}
                            </h4>
                            <div className="bg-amber-500/20 text-amber-300 text-xs px-2 py-1 rounded-full mb-2 border border-amber-500/30">
                              {collectible.status_effect}
                            </div>
                            <p className="text-purple-200 text-xs line-clamp-2" title={collectible.description}>
                              {collectible.description}
                            </p>
                          </div>
                        </div>
                        <div className="absolute -top-2 -right-2 bg-amber-400 text-black text-xs font-bold rounded-full w-6 h-6 flex items-center justify-center shadow-lg">
                          {index}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default GameSandbox
