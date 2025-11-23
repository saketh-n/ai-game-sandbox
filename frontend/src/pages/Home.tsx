import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAssetContext } from '../context/AssetContext'
import Header from '../components/Header'
import PromptInput from '../components/PromptInput'
import CachedPrompts from '../components/CachedPrompts'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorMessage from '../components/ErrorMessage'
import AssetPromptsDisplay from '../components/AssetPromptsDisplay'

const API_URL = 'http://localhost:8000'

interface CachedPrompt {
  prompt: string
  timestamp: string
  preview: string
}

const Home = () => {
  const navigate = useNavigate()
  const { setAssetData, setSelectedPrompts, setOriginalTheme } = useAssetContext()

  const [prompt, setPrompt] = useState('')
  const [submittedPrompt, setSubmittedPrompt] = useState('')
  const [generatedResponse, setGeneratedResponse] = useState('')
  const [parsedData, setParsedData] = useState<any>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [cachedPrompts, setCachedPrompts] = useState<CachedPrompt[]>([])
  const [showCachedPrompts, setShowCachedPrompts] = useState(false)
  const [isCached, setIsCached] = useState(false)

  useEffect(() => {
    fetchCachedPrompts()
  }, [])

  const fetchCachedPrompts = async () => {
    try {
      const response = await fetch(`${API_URL}/cached-prompts`)
      if (response.ok) {
        const data = await response.json()
        setCachedPrompts(data.prompts)
        setShowCachedPrompts(data.count > 0)
      }
    } catch (err) {
      console.error('Failed to fetch cached prompts:', err)
    }
  }

  const clearCache = async () => {
    if (!window.confirm('Are you sure you want to clear all cached prompts?')) {
      return
    }

    try {
      const response = await fetch(`${API_URL}/cache`, {
        method: 'DELETE',
      })

      if (response.ok) {
        setCachedPrompts([])
        setShowCachedPrompts(false)
        alert('Cache cleared successfully!')
      } else {
        alert('Failed to clear cache')
      }
    } catch (err) {
      console.error('Failed to clear cache:', err)
      alert('Error clearing cache')
    }
  }

  const loadCachedPrompt = async (cachedPrompt: string) => {
    setIsLoading(true)
    setError('')
    setGeneratedResponse('')
    setParsedData(null)
    setShowCachedPrompts(false)

    try {
      const response = await fetch(`${API_URL}/fetch-cached-prompt`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: cachedPrompt }),
      })

      if (!response.ok) throw new Error(`API error: ${response.status}`)

      const data = await response.json()
      setSubmittedPrompt(data.prompt)
      setPrompt(data.prompt)
      setGeneratedResponse(data.result)
      setIsCached(true)

      const parsed = parseJSON(data.result)
      if (parsed) {
        setParsedData(parsed)
        setAssetData(parsed)
        setOriginalTheme(data.prompt)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load cached prompt')
    } finally {
      setIsLoading(false)
    }
  }

  const generateAssetPrompts = async (userPrompt: string) => {
    setIsLoading(true)
    setError('')
    setSubmittedPrompt(userPrompt)
    setGeneratedResponse('')
    setParsedData(null)
    setIsCached(false)
    setShowCachedPrompts(false)

    try {
      const response = await fetch(`${API_URL}/generate-asset-prompts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: userPrompt }),
      })

      if (!response.ok) throw new Error(`API error: ${response.status}`)

      const data = await response.json()
      setIsCached(data.cached || false)
      setGeneratedResponse(data.result)
      fetchCachedPrompts()

      const parsed = parseJSON(data.result)
      if (parsed) {
        setParsedData(parsed)
        setAssetData(parsed)
        setOriginalTheme(userPrompt)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate prompts')
    } finally {
      setIsLoading(false)
    }
  }

  const parseJSON = (text: string) => {
    try {
      let cleanedJson = text.trim()
      if (cleanedJson.startsWith('```json')) {
        cleanedJson = cleanedJson.replace(/^```json\s*/, '').replace(/\s*```$/, '')
      } else if (cleanedJson.startsWith('```')) {
        cleanedJson = cleanedJson.replace(/^```\s*/, '').replace(/\s*```$/, '')
      }
      return JSON.parse(cleanedJson)
    } catch {
      return null
    }
  }

  const handleGenerateAssets = (selectedPromptsData: any[]) => {
    setSelectedPrompts(selectedPromptsData)
    navigate('/generate-assets')
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-indigo-900 to-blue-900">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-4xl mx-auto">
          <Header />

          <CachedPrompts
            cachedPrompts={cachedPrompts}
            showCachedPrompts={showCachedPrompts}
            onToggle={() => setShowCachedPrompts(!showCachedPrompts)}
            onSelectPrompt={loadCachedPrompt}
            onClearCache={clearCache}
          />

          <PromptInput
            prompt={prompt}
            isCached={isCached}
            onPromptChange={setPrompt}
            onSubmit={generateAssetPrompts}
          />

          {isLoading && <LoadingSpinner />}
          {error && <ErrorMessage message={error} />}

          {generatedResponse && !isLoading && (
            <>
              {parsedData ? (
                <AssetPromptsDisplay
                  data={parsedData}
                  originalTheme={submittedPrompt}
                  onGenerateAssets={handleGenerateAssets}
                />
              ) : (
                <ErrorMessage
                  message="Failed to parse JSON response"
                  details={generatedResponse}
                  isWarning
                />
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default Home

