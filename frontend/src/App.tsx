import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AssetProvider } from './context/AssetContext'
import Home from './pages/Home'
import GenerateAssets from './pages/GenerateAssets'

function App() {
  return (
    <AssetProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/generate-assets" element={<GenerateAssets />} />
        </Routes>
      </BrowserRouter>
    </AssetProvider>
  )
}

export default App
