import Tooltip from './Tooltip'
import './SignalCard.css'

function SignalCard({ signal, type = 'general', weight = null }) {
  const dirLabel = signal.direction === 'buy' ? 'BUY'
    : signal.direction === 'hold' ? 'HOLD'
    : signal.direction === 'avoid' ? 'AVOID'
    : 'NEUTRAL'

  return (
    <div className={`signal-card ${signal.direction}`}>
      <div className="card-header">
        <div className="signal-ticker-section">
          <div className="ticker-info">
            <span className="ticker-symbol">{signal.ticker}</span>
            {signal.sector && (
              <span className="ticker-sector">
                <Tooltip term="sector">{signal.sector}</Tooltip>
              </span>
            )}
          </div>
        </div>
        <div className="signal-direction-badge">
          <Tooltip term={signal.direction}>{dirLabel}</Tooltip>
        </div>
      </div>

      <div className="confidence-section">
        <div className="confidence-header">
          <span className="confidence-label">
            <Tooltip term="confidence">Confidence</Tooltip>
          </span>
          <span className="confidence-value">{signal.confidence}/10</span>
        </div>
        <div className="confidence-bars">
          {[...Array(10)].map((_, i) => (
            <div key={i} className={`bar ${i < signal.confidence ? 'filled' : ''}`} />
          ))}
        </div>
      </div>

      {weight !== null && weight !== undefined && (
        <div className="portfolio-weight">
          <span className="weight-label">Your position</span>
          <span className="weight-value">{(weight * 100).toFixed(1)}%</span>
        </div>
      )}

      {(signal.pe_ratio != null || signal.dividend_yield > 0) && (
        <div className="signal-cues">
          {signal.pe_ratio != null && (
            <span className="cue-badge">
              <Tooltip term="pe">P/E</Tooltip> {Number(signal.pe_ratio).toFixed(1)}
            </span>
          )}
          {signal.dividend_yield > 0 && (
            <span className="cue-badge positive">
              {(signal.dividend_yield * 100).toFixed(1)}% <Tooltip term="dividend">dividend</Tooltip>
            </span>
          )}
        </div>
      )}

      <div className="rationale-section">
        <p className="rationale-text">{signal.rationale}</p>
      </div>

      {signal.portfolio_context && (
        <div className="portfolio-context">
          <p>{signal.portfolio_context}</p>
        </div>
      )}
    </div>
  )
}

export default SignalCard
