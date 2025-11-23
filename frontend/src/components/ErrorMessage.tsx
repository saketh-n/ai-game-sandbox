interface ErrorMessageProps {
  message: string
  details?: string
  isWarning?: boolean
}

const ErrorMessage = ({ message, details, isWarning = false }: ErrorMessageProps) => {
  const bgColor = isWarning ? 'bg-yellow-500/10' : 'bg-red-500/10'
  const borderColor = isWarning ? 'border-yellow-500/20' : 'border-red-500/20'
  const iconColor = isWarning ? 'text-yellow-400' : 'text-red-400'
  const titleColor = isWarning ? 'text-yellow-300' : 'text-red-300'
  const textColor = isWarning ? 'text-yellow-200' : 'text-red-200'

  return (
    <div
      className={`${bgColor} backdrop-blur-lg rounded-2xl shadow-2xl p-8 border ${borderColor}`}
    >
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          <svg className={`w-6 h-6 ${iconColor}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d={
                isWarning
                  ? 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
                  : 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
              }
            />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className={`text-lg font-semibold ${titleColor} mb-2`}>
            {isWarning ? 'Warning' : 'Error'}
          </h3>
          <p className={textColor}>{message}</p>
          {details && (
            <div className="mt-4 text-purple-100 text-base leading-relaxed whitespace-pre-wrap font-mono text-sm">
              {details}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default ErrorMessage

