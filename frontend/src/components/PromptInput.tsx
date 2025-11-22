interface PromptInputProps {
  prompt: string
  isCached: boolean
  onPromptChange: (value: string) => void
  onSubmit: (prompt: string) => void
}

const PromptInput = ({ prompt, isCached, onPromptChange, onSubmit }: PromptInputProps) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (prompt.trim()) {
      onSubmit(prompt)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && prompt.trim()) {
      onSubmit(prompt)
    }
  }

  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 mb-8 border border-white/20">
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <input
            type="text"
            value={prompt}
            onChange={(e) => onPromptChange(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Enter video game theme here..."
            className="w-full px-6 py-4 text-lg bg-white/90 rounded-xl border-2 border-purple-300 focus:border-purple-500 focus:outline-none focus:ring-4 focus:ring-purple-500/20 transition-all duration-200 placeholder-gray-400"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">
            Press Enter
          </div>
        </div>
      </form>
      {isCached && (
        <div className="mt-3 flex items-center space-x-2 text-green-400 text-sm">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <span>Loaded from cache (instant!)</span>
        </div>
      )}
    </div>
  )
}

export default PromptInput

