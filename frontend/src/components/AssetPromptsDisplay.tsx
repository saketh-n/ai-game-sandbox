import { useState } from 'react'

interface Variation {
  description?: string
  variations: string[]
}

interface EnvironmentAssets {
  key_elements_needed: string[]
  assets: {
    [key: string]: {
      variations: string[]
    }
  }
}

interface NPCs {
  categories: {
    [key: string]: {
      variations: string[]
    }
  }
}

interface AssetData {
  main_character?: Variation
  environment_assets?: EnvironmentAssets
  npcs?: NPCs
  backgrounds?: {
    scenes: string[]
  }
}

interface AssetPromptsDisplayProps {
  data: AssetData
  originalTheme: string
}

const AssetPromptsDisplay: React.FC<AssetPromptsDisplayProps> = ({ data, originalTheme }) => {
  const [openSections, setOpenSections] = useState<{ [key: string]: boolean }>({})
  const [editablePrompts, setEditablePrompts] = useState<{ [key: string]: string }>({})

  const toggleSection = (section: string) => {
    setOpenSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  const updatePrompt = (key: string, value: string) => {
    setEditablePrompts(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const getPromptValue = (key: string, defaultValue: string) => {
    return editablePrompts[key] !== undefined ? editablePrompts[key] : defaultValue
  }

  const renderEditablePrompt = (prompt: string, promptKey: string, index: number) => {
    return (
      <div key={`${promptKey}-${index}`} className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-purple-300">Variation {index + 1}</span>
          <button
            onClick={() => navigator.clipboard.writeText(getPromptValue(promptKey, prompt))}
            className="text-xs px-3 py-1 bg-purple-500/20 hover:bg-purple-500/30 text-purple-200 rounded-lg transition-colors"
          >
            Copy
          </button>
        </div>
        <textarea
          value={getPromptValue(promptKey, prompt)}
          onChange={(e) => updatePrompt(promptKey, e.target.value)}
          className="w-full px-4 py-3 bg-white/5 border border-purple-400/30 rounded-lg text-purple-100 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 resize-y min-h-[100px] font-mono"
        />
      </div>
    )
  }

  const renderCollapsibleSection = (title: string, sectionKey: string, content: React.ReactNode) => {
    const isOpen = openSections[sectionKey]
    return (
      <div className="mb-4">
        <button
          onClick={() => toggleSection(sectionKey)}
          className="w-full flex items-center justify-between px-4 py-3 bg-purple-500/20 hover:bg-purple-500/30 rounded-lg transition-colors group"
        >
          <span className="text-lg font-semibold text-white">{title}</span>
          <svg
            className={`w-5 h-5 text-purple-300 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {isOpen && (
          <div className="mt-3 pl-4 border-l-2 border-purple-500/30">
            {content}
          </div>
        )}
      </div>
    )
  }

  const renderSubSection = (title: string, sectionKey: string, content: React.ReactNode) => {
    const isOpen = openSections[sectionKey]
    return (
      <div className="mb-3">
        <button
          onClick={() => toggleSection(sectionKey)}
          className="w-full flex items-center justify-between px-3 py-2 bg-indigo-500/20 hover:bg-indigo-500/30 rounded-lg transition-colors"
        >
          <span className="text-base font-medium text-purple-200">{title}</span>
          <svg
            className={`w-4 h-4 text-purple-300 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        {isOpen && (
          <div className="mt-2 pl-3">
            {content}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20 animate-fade-in">
      {/* Header */}
      <div className="flex items-start space-x-3 mb-6">
        <div className="flex-shrink-0">
          <svg
            className="w-6 h-6 text-green-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-bold text-white mb-2">
            Generated Asset Prompts
          </h3>
          <div className="text-sm text-purple-300 mb-4">
            Theme: "{originalTheme}"
          </div>
        </div>
      </div>

      {/* Main Character Section */}
      {data.main_character && renderCollapsibleSection(
        '🎮 Main Character',
        'main-character',
        <div>
          {data.main_character.description && (
            <div className="mb-4 p-3 bg-indigo-500/10 rounded-lg">
              <span className="text-sm font-medium text-purple-300">Description:</span>
              <p className="text-purple-100 text-sm mt-1">{data.main_character.description}</p>
            </div>
          )}
          <div className="space-y-2">
            {data.main_character.variations.map((variation, index) =>
              renderEditablePrompt(variation, `main-character-${index}`, index)
            )}
          </div>
        </div>
      )}

      {/* Environment Assets Section */}
      {data.environment_assets && renderCollapsibleSection(
        '🌍 Environment Assets',
        'environment',
        <div>
          {data.environment_assets.key_elements_needed && (
            <div className="mb-4 p-3 bg-indigo-500/10 rounded-lg">
              <span className="text-sm font-medium text-purple-300">Key Elements:</span>
              <div className="flex flex-wrap gap-2 mt-2">
                {data.environment_assets.key_elements_needed.map((element, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-purple-500/20 text-purple-200 text-xs rounded-full"
                  >
                    {element}
                  </span>
                ))}
              </div>
            </div>
          )}
          <div className="space-y-3">
            {Object.entries(data.environment_assets.assets).map(([assetKey, assetData]) =>
              renderSubSection(
                assetKey.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '),
                `env-${assetKey}`,
                <div className="space-y-2">
                  {assetData.variations.map((variation, index) =>
                    renderEditablePrompt(variation, `env-${assetKey}-${index}`, index)
                  )}
                </div>
              )
            )}
          </div>
        </div>
      )}

      {/* NPCs Section */}
      {data.npcs && renderCollapsibleSection(
        '👥 NPCs',
        'npcs',
        <div className="space-y-3">
          {Object.entries(data.npcs.categories).map(([category, categoryData]) =>
            renderSubSection(
              category.charAt(0).toUpperCase() + category.slice(1),
              `npc-${category}`,
              <div className="space-y-2">
                {categoryData.variations.map((variation, index) =>
                  renderEditablePrompt(variation, `npc-${category}-${index}`, index)
                )}
              </div>
            )
          )}
        </div>
      )}

      {/* Backgrounds Section */}
      {data.backgrounds && renderCollapsibleSection(
        '🎨 Background Scenes',
        'backgrounds',
        <div className="space-y-2">
          {data.backgrounds.scenes.map((scene, index) =>
            renderEditablePrompt(scene, `background-${index}`, index)
          )}
        </div>
      )}
    </div>
  )
}

export default AssetPromptsDisplay

