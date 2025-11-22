import { useState } from 'react'
import { AssetData, SelectedPrompt } from '../context/AssetContext'

interface AssetPromptsDisplayProps {
  data: AssetData
  originalTheme: string
  onGenerateAssets: (selectedPrompts: SelectedPrompt[]) => void
}

const AssetPromptsDisplay: React.FC<AssetPromptsDisplayProps> = ({ data, originalTheme, onGenerateAssets }) => {
  const [openSections, setOpenSections] = useState<{ [key: string]: boolean }>({})
  const [editablePrompts, setEditablePrompts] = useState<{ [key: string]: string }>({})
  
  // Initialize with first variant selected for each group
  const initializeDefaultSelections = (): { [key: string]: string } => {
    const defaults: { [key: string]: string } = {}
    
    // Main character - select first variation
    if (data.main_character && data.main_character.variations.length > 0) {
      defaults['main-character'] = 'main-character-0'
    }
    
    // Background - select first variation
    if (data.background && data.background.variations.length > 0) {
      defaults['background'] = 'background-0'
    }
    
    // Collectible item - select first variation
    if (data.collectible_item && data.collectible_item.variations.length > 0) {
      defaults['collectible-item'] = 'collectible-item-0'
    }
    
    return defaults
  }
  
  const [selectedVariants, setSelectedVariants] = useState<{ [key: string]: string }>(initializeDefaultSelections())

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

  const selectVariant = (groupKey: string, variantKey: string) => {
    setSelectedVariants(prev => ({
      ...prev,
      [groupKey]: variantKey
    }))
  }

  const isVariantSelected = (groupKey: string, variantKey: string) => {
    return selectedVariants[groupKey] === variantKey
  }

  const formatCategoryName = (groupKey: string): string => {
    if (groupKey === 'main-character') return 'Main Character'
    if (groupKey === 'background') return 'Background'
    if (groupKey === 'collectible-item') return 'Collectible Item'
    return groupKey
  }

  const collectSelectedPrompts = (): SelectedPrompt[] => {
    const selectedPrompts: SelectedPrompt[] = []
    
    Object.entries(selectedVariants).forEach(([groupKey, variantKey]) => {
      // Get the actual prompt text (check if it was edited)
      const originalPrompt = getOriginalPrompt(groupKey, variantKey)
      const promptText = getPromptValue(variantKey, originalPrompt)
      
      selectedPrompts.push({
        category: formatCategoryName(groupKey),
        groupKey: groupKey,
        prompt: promptText
      })
    })
    
    return selectedPrompts
  }

  const getOriginalPrompt = (groupKey: string, variantKey: string): string => {
    // Extract the original prompt from the data based on the variant key
    const index = parseInt(variantKey.split('-').pop() || '0')
    
    if (groupKey === 'main-character' && data.main_character) {
      return data.main_character.variations[index] || ''
    }
    
    if (groupKey === 'background' && data.background) {
      return data.background.variations[index] || ''
    }
    
    if (groupKey === 'collectible-item' && data.collectible_item) {
      return data.collectible_item.variations[index] || ''
    }
    
    return ''
  }

  const handleGenerateAssets = () => {
    const selectedPrompts = collectSelectedPrompts()
    console.log('Generate Assets clicked!')
    console.log('Selected prompts:', selectedPrompts)
    onGenerateAssets(selectedPrompts)
  }

  const renderEditablePrompt = (prompt: string, promptKey: string, index: number, groupKey: string) => {
    const isSelected = isVariantSelected(groupKey, promptKey)
    
    return (
      <div key={`${promptKey}-${index}`} className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center space-x-3">
            <label className="flex items-center cursor-pointer group">
              <input
                type="radio"
                name={groupKey}
                checked={isSelected}
                onChange={() => selectVariant(groupKey, promptKey)}
                className="w-4 h-4 text-purple-500 bg-white/10 border-purple-400 focus:ring-purple-500 focus:ring-2 cursor-pointer"
              />
              <span className="ml-2 text-sm font-medium text-purple-300 group-hover:text-purple-200">
                Variation {index + 1}
              </span>
            </label>
          </div>
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
          className={`w-full px-4 py-3 bg-white/5 border rounded-lg text-purple-100 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-purple-500/50 resize-y min-h-[100px] font-mono transition-colors ${
            isSelected 
              ? 'border-purple-500 bg-purple-500/5' 
              : 'border-purple-400/30 focus:border-purple-500/50'
          }`}
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
              renderEditablePrompt(variation, `main-character-${index}`, index, 'main-character')
            )}
          </div>
        </div>
      )}

      {/* Background Section */}
      {data.background && renderCollapsibleSection(
        '🌍 Background',
        'background',
        <div>
          {data.background.description && (
            <div className="mb-4 p-3 bg-indigo-500/10 rounded-lg">
              <span className="text-sm font-medium text-purple-300">Description:</span>
              <p className="text-purple-100 text-sm mt-1">{data.background.description}</p>
            </div>
          )}
          <div className="space-y-2">
            {data.background.variations.map((variation, index) =>
              renderEditablePrompt(variation, `background-${index}`, index, 'background')
            )}
          </div>
        </div>
      )}

      {/* Collectible Item Section */}
      {data.collectible_item && renderCollapsibleSection(
        '💎 Collectible Item',
        'collectible-item',
        <div>
          {data.collectible_item.description && (
            <div className="mb-4 p-3 bg-indigo-500/10 rounded-lg">
              <span className="text-sm font-medium text-purple-300">Description:</span>
              <p className="text-purple-100 text-sm mt-1">{data.collectible_item.description}</p>
            </div>
          )}
          <div className="space-y-2">
            {data.collectible_item.variations.map((variation, index) =>
              renderEditablePrompt(variation, `collectible-item-${index}`, index, 'collectible-item')
            )}
          </div>
        </div>
      )}

      {/* Generate Assets Button */}
      <div className="mt-8 pt-6 border-t border-purple-500/30">
        <button
          onClick={handleGenerateAssets}
          className="w-full px-6 py-4 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-semibold text-lg rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02] active:scale-[0.98] flex items-center justify-center space-x-3"
        >
          <svg 
            className="w-6 h-6" 
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
          <span>Generate Assets</span>
        </button>
        <p className="text-center text-purple-300 text-sm mt-3">
          First variation selected by default. Change selections as needed, then click to generate images
        </p>
      </div>
    </div>
  )
}

export default AssetPromptsDisplay

