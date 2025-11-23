interface CachedPrompt {
  prompt: string
  timestamp: string
  preview: string
}

interface CachedPromptsProps {
  cachedPrompts: CachedPrompt[]
  showCachedPrompts: boolean
  onToggle: () => void
  onSelectPrompt: (prompt: string) => void
  onClearCache: () => void
}

const CachedPrompts = ({
  cachedPrompts,
  showCachedPrompts,
  onToggle,
  onSelectPrompt,
  onClearCache,
}: CachedPromptsProps) => {
  if (cachedPrompts.length === 0) {
    return null
  }

  return (
    <>
      {showCachedPrompts ? (
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-6 mb-8 border border-white/20">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white flex items-center space-x-2">
              <svg
                className="w-5 h-5 text-purple-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span>Recent Prompts ({cachedPrompts.length})</span>
            </h3>
            <div className="flex items-center space-x-3">
              <button
                onClick={onClearCache}
                className="px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-200 rounded-lg transition-colors text-sm flex items-center space-x-2 border border-red-500/30"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
                <span>Clear</span>
              </button>
              <button
                onClick={onToggle}
                className="text-purple-300 hover:text-purple-200 text-sm transition-colors"
              >
                Hide
              </button>
            </div>
          </div>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {cachedPrompts.map((cached, index) => (
              <button
                key={index}
                onClick={() => onSelectPrompt(cached.prompt)}
                className="w-full text-left px-4 py-3 bg-purple-500/10 hover:bg-purple-500/20 rounded-lg transition-colors border border-purple-500/20 hover:border-purple-500/40 group"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 mr-3">
                    <p className="text-purple-100 text-sm font-medium group-hover:text-white transition-colors">
                      {cached.preview}
                    </p>
                    <p className="text-purple-400 text-xs mt-1">
                      {new Date(cached.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <svg
                    className="w-5 h-5 text-purple-400 group-hover:text-purple-300 flex-shrink-0"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </div>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <button
          onClick={onToggle}
          className="mb-8 px-4 py-2 bg-purple-500/20 hover:bg-purple-500/30 text-purple-200 rounded-lg transition-colors text-sm flex items-center space-x-2"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span>
            Show {cachedPrompts.length} cached prompt{cachedPrompts.length !== 1 ? 's' : ''}
          </span>
        </button>
      )}
    </>
  )
}

export default CachedPrompts

