import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AssetProvider } from './context/AssetContext'
import Home from './pages/Home'
import GenerateAssets from './pages/GenerateAssets'
import GameSandbox from './pages/GameSandbox'

function App() {
  return (
    <AssetProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/generate-assets" element={<GenerateAssets />} />
          <Route path="/game-sandbox" element={<GameSandbox />} />
        </Routes>
      </BrowserRouter>
    </AssetProvider>
  )
}

export default App
