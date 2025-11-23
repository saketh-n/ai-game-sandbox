import { createContext, useContext, useState, ReactNode } from 'react'

interface MainCharacterVariation {
  prompt: string
  style: string
  additional_instructions: string
}

interface BackgroundVariation {
  prompt: string
  image_size: string
  output_format: string
}

interface CollectibleVariation {
  prompt: string
  style: string
  output_format: string
}

export interface AssetData {
  main_character?: {
    description?: string
    variations: MainCharacterVariation[]
  }
  background?: {
    description?: string
    variations: BackgroundVariation[]
  }
  collectible_item?: {
    description?: string
    variations: CollectibleVariation[]
  }
}

export interface SelectedPrompt {
  category: string
  groupKey: string
  prompt: string
  style?: string
  additional_instructions?: string
  image_size?: string
  output_format?: string
}

export interface GeneratedAssetImages {
  mainCharacter?: string
  background?: string
  collectible?: string
}

interface AssetContextType {
  assetData: AssetData | null
  setAssetData: (data: AssetData | null) => void
  selectedPrompts: SelectedPrompt[]
  setSelectedPrompts: (prompts: SelectedPrompt[]) => void
  originalTheme: string
  setOriginalTheme: (theme: string) => void
  generatedImages: GeneratedAssetImages
  setGeneratedImages: (images: GeneratedAssetImages) => void
}

const AssetContext = createContext<AssetContextType | undefined>(undefined)

export const AssetProvider = ({ children }: { children: ReactNode }) => {
  const [assetData, setAssetData] = useState<AssetData | null>(null)
  const [selectedPrompts, setSelectedPrompts] = useState<SelectedPrompt[]>([])
  const [originalTheme, setOriginalTheme] = useState('')
  const [generatedImages, setGeneratedImages] = useState<GeneratedAssetImages>({})

  return (
    <AssetContext.Provider
      value={{
        assetData,
        setAssetData,
        selectedPrompts,
        setSelectedPrompts,
        originalTheme,
        setOriginalTheme,
        generatedImages,
        setGeneratedImages,
      }}
    >
      {children}
    </AssetContext.Provider>
  )
}

export const useAssetContext = () => {
  const context = useContext(AssetContext)
  if (context === undefined) {
    throw new Error('useAssetContext must be used within an AssetProvider')
  }
  return context
}

