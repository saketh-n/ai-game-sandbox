import { useNavigate } from 'react-router-dom'
import { useAssetContext } from '../context/AssetContext'
import { useEffect, useState } from 'react'

const API_URL = 'http://localhost:8000'

interface AssetGeneration {
  prompt: string
  category: string
  groupKey: string
  style?: string
  additional_instructions?: string
  image_size?: string
  output_format?: string
  status: 'pending' | 'generating' | 'completed' | 'error'
  imageUrl?: string
  error?: string
  cached?: boolean
}

const GenerateAssets = () => {
  const navigate = useNavigate()
  const { selectedPrompts } = useAssetContext()
  const [assets, setAssets] = useState<AssetGeneration[]>([])

  useEffect(() => {
    if (selectedPrompts.length === 0) {
      navigate('/')
      return
    }

    // Initialize assets with pending status
    const initialAssets = selectedPrompts.map(sp => ({
      prompt: sp.prompt,
      category: sp.category,
      groupKey: sp.groupKey,
      style: sp.style,
      additional_instructions: sp.additional_instructions,
      image_size: sp.image_size,
      output_format: sp.output_format,
      status: 'pending' as const,
    }))
    setAssets(initialAssets)

    // Start generating images
    generateAllImages(initialAssets)
  }, [selectedPrompts, navigate])

  const generateSingleImage = async (
    index: number, 
    assetData: AssetGeneration,
    forceRegenerate: boolean = false
  ) => {
    // Use the passed asset instead of reading from state
    const asset = assetData
    
    if (!asset) {
      console.error(`Asset at index ${index} is undefined`)
      return
    }
    
    // Update status to generating
    setAssets(prev => prev.map((a, idx) => 
      idx === index ? { ...a, status: 'generating', cached: false } : a
    ))
    
    try {
      const response = await fetch(`${API_URL}/generate-image-asset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: asset.prompt,
          category: asset.category,
          style: asset.style || '',
          additional_instructions: asset.additional_instructions || '',
          image_size: asset.image_size || '',
          output_format: asset.output_format || 'png',
          force_regenerate: forceRegenerate,
        }),
      })
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(`API error: ${response.status} - ${errorData.detail || response.statusText}`)
      }
      
      const data = await response.json()
      
      // Update status to completed with image URL and cached flag
      setAssets(prev => prev.map((a, idx) => 
        idx === index ? { 
          ...a, 
          status: 'completed', 
          imageUrl: data.image_url,
          cached: data.cached || false
        } : a
      ))
    } catch (error) {
      console.error(`Error generating asset at index ${index}:`, error)
      // Update status to error
      setAssets(prev => prev.map((a, idx) => 
        idx === index ? { 
          ...a, 
          status: 'error', 
          error: error instanceof Error ? error.message : 'Failed to generate'
        } : a
      ))
    }
  }
  
  const generateAllImages = async (initialAssets: AssetGeneration[]) => {
    // Pass the actual asset data to each generation call
    const generationPromises = initialAssets.map((asset, index) => 
      generateSingleImage(index, asset, false)
    )
    await Promise.all(generationPromises)
  }
  
  const handleRefresh = (index: number) => {
    const asset = assets[index]
    if (asset) {
      generateSingleImage(index, asset, true)
    }
  }

  const handleBack = () => {
    navigate('/')
  }

  const completedCount = assets.filter(a => a.status === 'completed').length
  const generatingCount = assets.filter(a => a.status === 'generating').length
  const errorCount = assets.filter(a => a.status === 'error').length

  if (selectedPrompts.length === 0) {
    return null
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20 animate-fade-in">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-3">
                <svg
                  className="w-6 h-6 text-purple-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
                <h3 className="text-2xl font-bold text-white">Generating Assets</h3>
              </div>
              <button
                onClick={handleBack}
                className="px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-200 rounded-lg transition-colors flex items-center space-x-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                <span>Back to Prompts</span>
              </button>
            </div>

            {/* Progress Info */}
            <div className="mb-6 p-4 bg-indigo-500/10 rounded-lg border border-indigo-500/20">
              <div className="flex items-center space-x-3">
                <div className="flex-shrink-0">
                  {completedCount === assets.length ? (
                    <svg className="w-10 h-10 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  ) : (
                    <div className="relative w-10 h-10">
                      <div className="absolute inset-0 border-4 border-purple-400/30 rounded-full"></div>
                      <div className="absolute inset-0 border-4 border-transparent border-t-purple-400 rounded-full animate-spin"></div>
                    </div>
                  )}
                </div>
                <div className="flex-1">
                  <p className="text-white font-medium">
                    {completedCount === assets.length 
                      ? 'All assets generated!' 
                      : `Generating ${assets.length} assets...`}
                  </p>
                  <p className="text-purple-300 text-sm">
                    {completedCount} completed · {generatingCount} generating · {errorCount} errors
                  </p>
                </div>
              </div>
            </div>

            {/* Asset List */}
            <div className="space-y-4">
              {assets.map((asset, index) => (
                <div key={index} className="p-4 bg-white/5 rounded-xl border border-purple-400/30">
                  <div className="flex items-start space-x-4">
                    {/* Status Indicator */}
                    <div className="flex-shrink-0 mt-1">
                      {asset.status === 'generating' && (
                        <div className="relative w-8 h-8">
                          <div className="absolute inset-0 border-3 border-purple-400/30 rounded-full"></div>
                          <div className="absolute inset-0 border-3 border-transparent border-t-purple-400 rounded-full animate-spin"></div>
                        </div>
                      )}
                      {asset.status === 'completed' && (
                        <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      )}
                      {asset.status === 'error' && (
                        <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      )}
                      {asset.status === 'pending' && (
                        <div className="w-8 h-8 rounded-full bg-gray-500/20 flex items-center justify-center">
                          <div className="w-3 h-3 rounded-full bg-gray-400"></div>
                        </div>
                      )}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center space-x-2">
                          <span className="px-3 py-1 bg-purple-500/20 text-purple-200 text-xs font-medium rounded-full">
                            {asset.category}
                          </span>
                          {asset.status === 'generating' && (
                            <span className="text-yellow-400 text-xs font-medium">Generating...</span>
                          )}
                          {asset.status === 'completed' && !asset.cached && (
                            <span className="text-green-400 text-xs font-medium">Completed</span>
                          )}
                          {asset.status === 'completed' && asset.cached && (
                            <span className="flex items-center space-x-1 text-blue-400 text-xs font-medium">
                              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
                              </svg>
                              <span>Cached</span>
                            </span>
                          )}
                          {asset.status === 'error' && (
                            <span className="text-red-400 text-xs font-medium">Failed</span>
                          )}
                          {asset.status === 'pending' && (
                            <span className="text-gray-400 text-xs font-medium">Pending...</span>
                          )}
                        </div>
                        
                        {/* Refresh Button - Only show when completed or error */}
                        {(asset.status === 'completed' || asset.status === 'error') && (
                          <button
                            onClick={() => handleRefresh(index)}
                            className="px-3 py-1.5 bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-200 rounded-lg transition-colors flex items-center space-x-1.5 text-xs font-medium group"
                            title="Regenerate this image"
                          >
                            <svg className="w-3.5 h-3.5 group-hover:rotate-180 transition-transform duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            <span>Refresh</span>
                          </button>
                        )}
                      </div>

                      {/* Image Display */}
                      {asset.status === 'completed' && asset.imageUrl && (
                        <div className="mb-3">
                          <img 
                            src={asset.imageUrl} 
                            alt={asset.category}
                            className="w-full max-w-md rounded-lg border-2 border-purple-500/30"
                          />
                        </div>
                      )}

                      {/* Error Message */}
                      {asset.status === 'error' && asset.error && (
                        <div className="mb-2 p-2 bg-red-500/10 rounded border border-red-500/30">
                          <p className="text-red-300 text-xs">{asset.error}</p>
                        </div>
                      )}

                      {/* Prompt Details - All JSON Fields */}
                      <div className="space-y-3 mt-3">
                        {/* Main Prompt */}
                        <div>
                          <div className="text-xs font-semibold text-purple-300 uppercase tracking-wide mb-1">
                            Main Prompt
                          </div>
                          <div className="text-purple-100 text-sm leading-relaxed font-mono bg-white/5 p-3 rounded border border-purple-400/20">
                            {asset.prompt}
                          </div>
                        </div>

                        {/* Style */}
                        {asset.style && (
                          <div>
                            <div className="text-xs font-semibold text-blue-300 uppercase tracking-wide mb-1">
                              Style
                            </div>
                            <div className="text-blue-100 text-sm leading-relaxed font-mono bg-blue-500/5 p-3 rounded border border-blue-400/20">
                              {asset.style}
                            </div>
                          </div>
                        )}

                        {/* Additional Instructions */}
                        {asset.additional_instructions && (
                          <div>
                            <div className="text-xs font-semibold text-indigo-300 uppercase tracking-wide mb-1">
                              Additional Instructions
                            </div>
                            <div className="text-indigo-100 text-sm leading-relaxed font-mono bg-indigo-500/5 p-3 rounded border border-indigo-400/20">
                              {asset.additional_instructions}
                            </div>
                          </div>
                        )}

                        {/* Image Size */}
                        {asset.image_size && (
                          <div>
                            <div className="text-xs font-semibold text-green-300 uppercase tracking-wide mb-1">
                              Image Size
                            </div>
                            <div className="text-green-100 text-sm font-mono bg-green-500/5 p-2 rounded border border-green-400/20 inline-block">
                              {asset.image_size}
                            </div>
                          </div>
                        )}

                        {/* Output Format */}
                        {asset.output_format && (
                          <div>
                            <div className="text-xs font-semibold text-orange-300 uppercase tracking-wide mb-1">
                              Output Format
                            </div>
                            <div className="text-orange-100 text-sm font-mono bg-orange-500/5 p-2 rounded border border-orange-400/20 inline-block">
                              {asset.output_format}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Footer Info */}
            <div className="mt-6 p-4 bg-purple-500/10 rounded-lg border border-purple-500/20">
              <div className="flex items-start space-x-3">
                <svg
                  className="w-5 h-5 text-purple-300 flex-shrink-0 mt-0.5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <div className="flex-1">
                  <p className="text-purple-200 text-sm">
                    Assets are being generated using your selected prompts. Each image will appear
                    here once completed.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default GenerateAssets

