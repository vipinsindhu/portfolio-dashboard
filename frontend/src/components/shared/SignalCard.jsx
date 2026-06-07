import './SignalCard.css'

function SignalCard({ signal, type = 'general', weight = null }) {
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

  return (
    <div className={`signal-card ${signal.direction} ${type}`}>
      <div className="signal-header">
        <div className="signal-ticker">
          <span className="ticker-icon">{getDirectionIcon()}</span>
          <span className="ticker-symbol">{signal.ticker}</span>
        </div>
        <div className="signal-direction">{getDirectionLabel()}</div>
      </div>

      <div className="signal-confidence">
        <div className="confidence-label">Confidence</div>
        <div className="confidence-bars">
          {[...Array(10)].map((_, i) => (
            <div
              key={i}
              className={`bar ${i < signal.confidence ? 'filled' : ''}`}
            ></div>
          ))}
        </div>
        <span className="confidence-value">{signal.confidence}/10</span>
      </div>

      {weight !== null && weight !== undefined && (
        <div className="portfolio-weight">
          <span className="weight-label">Your Position:</span>
          <span className="weight-value">{(weight * 100).toFixed(1)}%</span>
        </div>
      )}

      <div className="signal-rationale">
        <p>{signal.rationale}</p>
      </div>

      {signal.portfolio_context && (
        <div className="portfolio-context">
          <p>{signal.portfolio_context}</p>
        </div>
      )}

      {signal.recommendation_type && (
        <div className="recommendation-type">
          <span className="rec-label">Action:</span>
          <span className="rec-value">{signal.recommendation_type.toUpperCase()}</span>
        </div>
      )}
    </div>
  )
}

export default SignalCard
