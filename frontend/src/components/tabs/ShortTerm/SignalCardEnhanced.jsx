import { useState, useEffect } from 'react'
import './SignalCardEnhanced.css'

function SignalCardEnhanced({ signal, type = 'general' }) {
  const [timeAgo, setTimeAgo] = useState('')
  const [isExpanded, setIsExpanded] = useState(false)

  useEffect(() => {
    const updateTimeAgo = () => {
      if (!signal.created_at) return

      const now = new Date()
      const created = new Date(signal.created_at)
      const diffMs = now - created
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      if (diffMins < 1) {
        setTimeAgo('just now')
      } else if (diffMins < 60) {
        setTimeAgo(`${diffMins}m ago`)
      } else if (diffHours < 24) {
        setTimeAgo(`${diffHours}h ago`)
      } else {
        setTimeAgo(`${diffDays}d ago`)
      }
    }

    updateTimeAgo()
    const interval = setInterval(updateTimeAgo, 30000)
    return () => clearInterval(interval)
  }, [signal.created_at])

  const getDirectionIcon = () => {
    switch (signal.direction) {
      case 'buy':
        return '🟢'
      case 'hold':
        return '⏸️'
      case 'avoid':
        return '🔴'
      default:
        return '📊'
    }
  }

  const getDirectionLabel = () => {
    switch (signal.direction) {
      case 'buy':
        return 'BUY'
      case 'hold':
        return 'HOLD'
      case 'avoid':
        return 'AVOID'
      default:
        return 'NEUTRAL'
    }
  }

  const getConfidenceColor = (confidence) => {
    if (confidence >= 8) return 'high'
    if (confidence >= 6) return 'medium'
    return 'low'
  }

  const confidenceLevel = getConfidenceColor(signal.confidence)
  const winRate = signal.accuracy_pct !== null && signal.accuracy_pct !== undefined
    ? signal.accuracy_pct
    : null

  return (
    <div className={`signal-card-enhanced ${signal.direction} ${type}`}>
      {/* Header */}
      <div className="card-header">
        <div className="signal-ticker-section">
          <span className="ticker-icon">{getDirectionIcon()}</span>
          <div className="ticker-info">
            <span className="ticker-symbol">{signal.ticker}</span>
            <span className="ticker-sector">{signal.sector || 'General'}</span>
          </div>
        </div>
        <div className="signal-direction-badge">
          {getDirectionLabel()}
        </div>
      </div>

      {/* Confidence */}
      <div className="confidence-section">
        <div className="confidence-header">
          <span className="confidence-label">Confidence</span>
          <span className={`confidence-value ${confidenceLevel}`}>
            {signal.confidence}/10
          </span>
        </div>
        <div className="confidence-bars">
          {[...Array(10)].map((_, i) => (
            <div
              key={i}
              className={`bar ${i < signal.confidence ? 'filled' : ''}`}
            />
          ))}
        </div>
      </div>

      {/* Rationale */}
      <div className="rationale-section">
        <p className={`rationale-text ${isExpanded ? 'expanded' : 'collapsed'}`}>
          {signal.rationale}
        </p>
        {signal.rationale && signal.rationale.length > 150 && (
          <button
            className="expand-button"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </div>

      {/* Meta Info */}
      <div className="meta-info">
        <span className="time-indicator">⏱️ {timeAgo}</span>
        {winRate !== null && (
          <span className={`win-rate ${winRate >= 80 ? 'high' : winRate >= 50 ? 'medium' : 'low'}`}>
            ✓ {winRate}% accuracy
          </span>
        )}
      </div>

      {/* Footer */}
      <div className="card-footer">
        <button
          className="btn-learn-more"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? '← Show Less' : 'Learn More →'}
        </button>
      </div>
    </div>
  )
}

export default SignalCardEnhanced
