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

  const collectSelectedPrompts = (): SelectedPrompt[] => {
    const selectedPrompts: SelectedPrompt[] = []
    
    // Collect main character (always index 0 since there's only one variation)
    if (data.main_character && data.main_character.variations.length > 0) {
      const variation = data.main_character.variations[0]
      const promptKey = 'main-character-0'
      selectedPrompts.push({
        category: 'Main Character',
        groupKey: 'main-character',
        prompt: getPromptValue(`${promptKey}-prompt`, variation.prompt),
        style: getPromptValue(`${promptKey}-style`, variation.style),
        additional_instructions: getPromptValue(`${promptKey}-additional_instructions`, variation.additional_instructions),
      })
    }
    
    // Collect background
    if (data.background && data.background.variations.length > 0) {
      const variation = data.background.variations[0]
      const promptKey = 'background-0'
      selectedPrompts.push({
        category: 'Background',
        groupKey: 'background',
        prompt: getPromptValue(`${promptKey}-prompt`, variation.prompt),
        image_size: getPromptValue(`${promptKey}-image_size`, variation.image_size),
        output_format: getPromptValue(`${promptKey}-output_format`, variation.output_format),
      })
    }
    
    // Collect collectible item
    if (data.collectible_item && data.collectible_item.variations.length > 0) {
      const variation = data.collectible_item.variations[0]
      const promptKey = 'collectible-item-0'
      selectedPrompts.push({
        category: 'Collectible Item',
        groupKey: 'collectible-item',
        prompt: getPromptValue(`${promptKey}-prompt`, variation.prompt),
        style: getPromptValue(`${promptKey}-style`, variation.style),
        output_format: getPromptValue(`${promptKey}-output_format`, variation.output_format),
      })
    }
    
    return selectedPrompts
  }

  const handleGenerateAssets = () => {
    const selectedPrompts = collectSelectedPrompts()
    console.log('Generate Assets clicked!')
    console.log('Selected prompts:', selectedPrompts)
    onGenerateAssets(selectedPrompts)
  }

  const renderEditablePrompt = (variation: any, promptKey: string, index: number) => {
    const copyFullJSON = () => {
      const fullObject: any = {
        prompt: getPromptValue(`${promptKey}-prompt`, variation.prompt || ''),
      }
      if (variation.style) fullObject.style = getPromptValue(`${promptKey}-style`, variation.style)
      if (variation.additional_instructions) fullObject.additional_instructions = getPromptValue(`${promptKey}-additional_instructions`, variation.additional_instructions)
      if (variation.image_size) fullObject.image_size = getPromptValue(`${promptKey}-image_size`, variation.image_size)
      if (variation.output_format) fullObject.output_format = getPromptValue(`${promptKey}-output_format`, variation.output_format)
      
      navigator.clipboard.writeText(JSON.stringify(fullObject, null, 2))
    }
    
    return (
      <div key={`${promptKey}-${index}`} className="mb-6 space-y-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-sm font-semibold text-purple-200">Prompt Configuration</h4>
          <button
            onClick={copyFullJSON}
            className="text-xs px-3 py-1.5 bg-purple-500/20 hover:bg-purple-500/30 text-purple-200 rounded-lg transition-colors flex items-center space-x-2"
          >
            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <span>Copy Full JSON</span>
          </button>
        </div>

        {/* Main Prompt Field */}
        <div className="space-y-2">
          <label className="text-xs font-medium text-purple-300 uppercase tracking-wide">Main Prompt</label>
          <textarea
            value={getPromptValue(`${promptKey}-prompt`, variation.prompt || '')}
            onChange={(e) => updatePrompt(`${promptKey}-prompt`, e.target.value)}
            placeholder="Enter the main image generation prompt..."
            className="w-full px-4 py-3 bg-white/5 border border-purple-400/30 focus:border-purple-500 rounded-lg text-purple-100 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-purple-500/50 resize-y min-h-[120px] font-mono transition-colors"
          />
        </div>

        {/* Style Field (if present) */}
        {variation.style !== undefined && (
          <div className="space-y-2">
            <label className="text-xs font-medium text-blue-300 uppercase tracking-wide">Style</label>
            <textarea
              value={getPromptValue(`${promptKey}-style`, variation.style || '')}
              onChange={(e) => updatePrompt(`${promptKey}-style`, e.target.value)}
              placeholder="Enter style description..."
              className="w-full px-4 py-3 bg-blue-500/5 border border-blue-400/30 focus:border-blue-500 rounded-lg text-blue-100 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-y min-h-[60px] font-mono transition-colors"
            />
          </div>
        )}

        {/* Additional Instructions Field (if present) */}
        {variation.additional_instructions !== undefined && (
          <div className="space-y-2">
            <label className="text-xs font-medium text-indigo-300 uppercase tracking-wide">Additional Instructions</label>
            <textarea
              value={getPromptValue(`${promptKey}-additional_instructions`, variation.additional_instructions || '')}
              onChange={(e) => updatePrompt(`${promptKey}-additional_instructions`, e.target.value)}
              placeholder="Enter additional instructions..."
              className="w-full px-4 py-3 bg-indigo-500/5 border border-indigo-400/30 focus:border-indigo-500 rounded-lg text-indigo-100 text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-indigo-500/50 resize-y min-h-[80px] font-mono transition-colors"
            />
          </div>
        )}

        {/* Image Size Field (if present) */}
        {variation.image_size !== undefined && (
          <div className="space-y-2">
            <label className="text-xs font-medium text-green-300 uppercase tracking-wide">Image Size</label>
            <input
              type="text"
              value={getPromptValue(`${promptKey}-image_size`, variation.image_size || '')}
              onChange={(e) => updatePrompt(`${promptKey}-image_size`, e.target.value)}
              placeholder="e.g., landscape_4_3"
              className="w-full px-4 py-2 bg-green-500/5 border border-green-400/30 focus:border-green-500 rounded-lg text-green-100 text-sm focus:outline-none focus:ring-2 focus:ring-green-500/50 font-mono transition-colors"
            />
          </div>
        )}

        {/* Output Format Field (if present) */}
        {variation.output_format !== undefined && (
          <div className="space-y-2">
            <label className="text-xs font-medium text-orange-300 uppercase tracking-wide">Output Format</label>
            <input
              type="text"
              value={getPromptValue(`${promptKey}-output_format`, variation.output_format || '')}
              onChange={(e) => updatePrompt(`${promptKey}-output_format`, e.target.value)}
              placeholder="e.g., png, jpg"
              className="w-full px-4 py-2 bg-orange-500/5 border border-orange-400/30 focus:border-orange-500 rounded-lg text-orange-100 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500/50 font-mono transition-colors"
            />
          </div>
        )}
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
              renderEditablePrompt(variation, `main-character-${index}`, index)
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
              renderEditablePrompt(variation, `background-${index}`, index)
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
              renderEditablePrompt(variation, `collectible-item-${index}`, index)
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
          Review and edit the prompts above, then click to generate images
        </p>
      </div>
    </div>
  )
}

export default AssetPromptsDisplay

