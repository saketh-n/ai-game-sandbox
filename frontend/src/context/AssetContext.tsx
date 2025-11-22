import { createContext, useContext, useState, ReactNode } from 'react'

export interface AssetData {
  main_character?: {
    description?: string
    variations: string[]
  }
  environment_assets?: {
    key_elements_needed: string[]
    assets: {
      [key: string]: {
        variations: string[]
      }
    }
  }
  npcs?: {
    categories: {
      [key: string]: {
        variations: string[]
      }
    }
  }
  backgrounds?: {
    scenes: string[]
  }
}

export interface SelectedPrompt {
  category: string
  groupKey: string
  prompt: string
}

interface AssetContextType {
  assetData: AssetData | null
  setAssetData: (data: AssetData | null) => void
  selectedPrompts: SelectedPrompt[]
  setSelectedPrompts: (prompts: SelectedPrompt[]) => void
  originalTheme: string
  setOriginalTheme: (theme: string) => void
}

const AssetContext = createContext<AssetContextType | undefined>(undefined)

export const AssetProvider = ({ children }: { children: ReactNode }) => {
  const [assetData, setAssetData] = useState<AssetData | null>(null)
  const [selectedPrompts, setSelectedPrompts] = useState<SelectedPrompt[]>([])
  const [originalTheme, setOriginalTheme] = useState('')

  return (
    <AssetContext.Provider
      value={{
        assetData,
        setAssetData,
        selectedPrompts,
        setSelectedPrompts,
        originalTheme,
        setOriginalTheme,
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

