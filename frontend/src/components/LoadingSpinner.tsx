const LoadingSpinner = () => {
  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20">
      <div className="flex items-center justify-center space-x-4">
        <div className="relative w-12 h-12">
          <div className="absolute inset-0 border-4 border-purple-400/30 rounded-full"></div>
          <div className="absolute inset-0 border-4 border-transparent border-t-purple-400 rounded-full animate-spin"></div>
        </div>
        <div className="text-white text-lg">Generating asset prompts with Claude AI...</div>
      </div>
    </div>
  )
}

export default LoadingSpinner

