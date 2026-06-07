import './SignalList.css'

function SignalList({ signals }) {
  if (!signals || signals.length === 0) {
    return (
      <div className="signal-list">
        <div className="no-signals">
          <p>No signals generated yet.</p>
          <p className="text-muted">Check back later for this week's stock recommendations.</p>
        </div>
      </div>
    )
  }

  const getDirectionColor = (direction) => {
    switch (direction.toLowerCase()) {
      case 'buy':
        return 'buy'
      case 'hold':
        return 'hold'
      case 'avoid':
        return 'avoid'
      default:
        return 'neutral'
    }
  }

  const getDirectionLabel = (direction) => {
    const dir = direction.toLowerCase()
    if (dir === 'buy') return '🟢 Buy'
    if (dir === 'hold') return '🟡 Hold'
    if (dir === 'avoid') return '🔴 Avoid'
    return direction
  }

  return (
    <div className="signal-list">
      <div className="signal-header">
        <h2>This Week's Signals</h2>
        <p className="signal-count">{signals.length} signals</p>
      </div>

      <div className="compliance-banner">
        <strong>⚠️ Disclaimer:</strong> These are general research signals, not personalized investment advice.
        See <a href="/disclaimer">full disclosure</a>.
      </div>

      <div className="signals-grid">
        {signals.map((signal) => (
          <div key={signal.id} className={`signal-card ${getDirectionColor(signal.direction)}`}>
            <div className="signal-ticker">
              <span className="ticker">{signal.ticker}</span>
              <span className={`direction ${getDirectionColor(signal.direction)}`}>
                {getDirectionLabel(signal.direction)}
              </span>
            </div>

            <div className="signal-confidence">
              <div className="confidence-label">Confidence</div>
              <div className="confidence-bar">
                <div
                  className="confidence-fill"
                  style={{ width: `${(signal.confidence / 10) * 100}%` }}
                />
              </div>
              <div className="confidence-score">{signal.confidence}/10</div>
            </div>

            <div className="signal-sector">
              <span className="sector-badge">{signal.sector || 'N/A'}</span>
            </div>

            <p className="signal-rationale">{signal.rationale}</p>

            <div className="signal-details">
              <span className="detail-item">
                Market Cap: <strong>{signal.market_cap || 'N/A'}</strong>
              </span>
              <span className="detail-item">
                Generated: <strong>{new Date(signal.created_at).toLocaleDateString()}</strong>
              </span>
            </div>

            <a href={`/signal/${signal.id}`} className="signal-link">
              View Details →
            </a>
          </div>
        ))}
      </div>
    </div>
  )
}

export default SignalList
