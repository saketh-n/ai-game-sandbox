import { useNavigate } from 'react-router-dom'
import { useAssetContext } from '../context/AssetContext'
import { useEffect } from 'react'

const GenerateAssets = () => {
  const navigate = useNavigate()
  const { selectedPrompts } = useAssetContext()

  useEffect(() => {
    if (selectedPrompts.length === 0) {
      navigate('/')
    }
  }, [selectedPrompts, navigate])

  const handleBack = () => {
    navigate('/')
  }

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
                  <div className="relative w-10 h-10">
                    <div className="absolute inset-0 border-4 border-purple-400/30 rounded-full"></div>
                    <div className="absolute inset-0 border-4 border-transparent border-t-purple-400 rounded-full animate-spin"></div>
                  </div>
                </div>
                <div className="flex-1">
                  <p className="text-white font-medium">
                    Generating {selectedPrompts.length} assets...
                  </p>
                  <p className="text-purple-300 text-sm">This may take a few moments</p>
                </div>
              </div>
            </div>

            {/* Asset List */}
            <div className="space-y-4">
              {selectedPrompts.map((item, index) => (
                <div key={index} className="p-4 bg-white/5 rounded-xl border border-purple-400/30">
                  <div className="flex items-start space-x-4">
                    {/* Loading Spinner */}
                    <div className="flex-shrink-0 mt-1">
                      <div className="relative w-8 h-8">
                        <div className="absolute inset-0 border-3 border-purple-400/30 rounded-full"></div>
                        <div className="absolute inset-0 border-3 border-transparent border-t-purple-400 rounded-full animate-spin"></div>
                      </div>
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="px-3 py-1 bg-purple-500/20 text-purple-200 text-xs font-medium rounded-full">
                          {item.category}
                        </span>
                        <span className="text-yellow-400 text-xs font-medium">Generating...</span>
                      </div>
                      <div className="text-purple-100 text-sm leading-relaxed line-clamp-3 font-mono">
                        {item.prompt}
                      </div>
                    </div>

                    {/* Status Icon */}
                    <div className="flex-shrink-0">
                      <div className="w-6 h-6 rounded-full bg-yellow-500/20 flex items-center justify-center">
                        <div className="w-2 h-2 rounded-full bg-yellow-400"></div>
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

