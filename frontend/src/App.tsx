import { useState } from 'react'
import AssetPromptsDisplay from './components/AssetPromptsDisplay'

const API_URL = 'http://localhost:8000'

interface AssetData {
  main_character?: any
  environment_assets?: any
  npcs?: any
  backgrounds?: any
}

function App() {
  const [prompt, setPrompt] = useState('')
  const [submittedPrompt, setSubmittedPrompt] = useState('')
  const [generatedResponse, setGeneratedResponse] = useState('')
  const [parsedData, setParsedData] = useState<AssetData | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const generateAssetPrompts = async (userPrompt: string) => {
    setIsLoading(true)
    setError('')
    setSubmittedPrompt(userPrompt)
    setGeneratedResponse('')
    setParsedData(null)

    try {
      const response = await fetch(`${API_URL}/generate-asset-prompts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: userPrompt }),
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const data = await response.json()
      const resultText = data.result
      setGeneratedResponse(resultText)

      // Try to parse the JSON response
      try {
        // Remove markdown code blocks if present
        let cleanedJson = resultText.trim()
        if (cleanedJson.startsWith('```json')) {
          cleanedJson = cleanedJson.replace(/^```json\s*/, '').replace(/\s*```$/, '')
        } else if (cleanedJson.startsWith('```')) {
          cleanedJson = cleanedJson.replace(/^```\s*/, '').replace(/\s*```$/, '')
        }
        
        const parsed = JSON.parse(cleanedJson)
        setParsedData(parsed)
      } catch (parseErr) {
        console.error('Failed to parse JSON response:', parseErr)
        // Keep the raw text in generatedResponse for display
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate prompts')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (prompt.trim()) {
      generateAssetPrompts(prompt)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && prompt.trim()) {
      generateAssetPrompts(prompt)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold text-white mb-4 tracking-tight">
              AI Video Game Asset Generator
            </h1>
            <p className="text-xl text-purple-200">
              Transform your imagination into game-ready assets with AI-powered generation and real-time sandboxing
            </p>
          </div>

          {/* Input Section */}
          <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 mb-8 border border-white/20">
            <form onSubmit={handleSubmit}>
              <div className="relative">
                <input
                  type="text"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Enter video game theme here..."
                  className="w-full px-6 py-4 text-lg bg-white/90 rounded-xl border-2 border-purple-300 focus:border-purple-500 focus:outline-none focus:ring-4 focus:ring-purple-500/20 transition-all duration-200 placeholder-gray-400"
                />
                <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">
                  Press Enter
                </div>
              </div>
            </form>
          </div>

          {/* Loading Section */}
          {isLoading && (
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20">
              <div className="flex items-center justify-center space-x-4">
                <div className="relative w-12 h-12">
                  <div className="absolute inset-0 border-4 border-purple-400/30 rounded-full"></div>
                  <div className="absolute inset-0 border-4 border-transparent border-t-purple-400 rounded-full animate-spin"></div>
                </div>
                <div className="text-white text-lg">
                  Generating asset prompts with Claude AI...
                </div>
              </div>
            </div>
          )}

          {/* Error Section */}
          {error && (
            <div className="bg-red-500/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-red-500/20">
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0">
                  <svg
                    className="w-6 h-6 text-red-400"
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
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-red-300 mb-2">
                    Error
                  </h3>
                  <p className="text-red-200">
                    {error}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Output Section */}
          {generatedResponse && !isLoading && (
            <>
              {parsedData ? (
                <AssetPromptsDisplay data={parsedData} originalTheme={submittedPrompt} />
              ) : (
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20 animate-fade-in">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0">
                      <svg
                        className="w-6 h-6 text-yellow-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                        />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-yellow-300 mb-2">
                        Raw Response (JSON Parse Failed)
                      </h3>
                      <div className="text-sm text-purple-300 mb-4">
                        Theme: "{submittedPrompt}"
                      </div>
                      <div className="text-purple-100 text-base leading-relaxed whitespace-pre-wrap font-mono text-sm">
                        {generatedResponse}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default App

