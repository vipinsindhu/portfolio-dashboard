import './PitfallDetector.css'

function PitfallDetector({ analysis }) {
  if (!analysis) {
    return null
  }

  const { summary, pitfalls, recommendations, risk_metrics, sector_allocation } = analysis

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'critical'
      case 'warning':
        return 'warning'
      default:
        return 'info'
    }
  }

  return (
    <div className="pitfall-detector-container">
      {/* Summary */}
      <div className="analysis-summary">
        <div className="summary-content">
          <h3>Portfolio Health</h3>
          <p className="summary-text">{summary}</p>
        </div>
      </div>

      {/* Risk Metrics Grid */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">Largest Position</div>
          <div className="metric-value">
            {(risk_metrics.largest_position_pct * 100).toFixed(1)}%
          </div>
          <div className="metric-hint">Recommended: &lt;15%</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Top 3 Holdings</div>
          <div className="metric-value">
            {(risk_metrics.top_3_concentration * 100).toFixed(1)}%
          </div>
          <div className="metric-hint">Recommended: &lt;50%</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Holdings</div>
          <div className="metric-value">{risk_metrics.holding_count}</div>
          <div className="metric-hint">Recommended: 15-30</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Portfolio Value</div>
          <div className="metric-value">${(risk_metrics.total_value / 1000).toFixed(1)}k</div>
          <div className="metric-hint">Total invested</div>
        </div>
      </div>

      {/* Sector Allocation */}
      <div className="sector-section">
        <h4>Sector Allocation</h4>
        <div className="sector-list">
          {Object.entries(sector_allocation)
            .sort((a, b) => b[1] - a[1])
            .map(([sector, percentage]) => (
              <div key={sector} className="sector-item">
                <div className="sector-name">{sector}</div>
                <div className="sector-bar-container">
                  <div
                    className="sector-bar"
                    style={{ width: `${percentage * 100}%` }}
                  ></div>
                </div>
                <div className="sector-percentage">
                  {(percentage * 100).toFixed(1)}%
                </div>
              </div>
            ))}
        </div>
      </div>

      {/* Pitfalls */}
      {pitfalls.length > 0 && (
        <div className="pitfalls-section">
          <h4>⚠️ Issues Detected</h4>

          {pitfalls.map((pitfall, idx) => (
            <div key={idx} className={`pitfall-card ${getSeverityColor(pitfall.severity)}`}>
              <div className="pitfall-header">
                <div className="pitfall-title">
                  <span className="pitfall-icon">
                    {pitfall.severity === 'critical' ? '🔴' : '🟡'}
                  </span>
                  <span>{pitfall.lesson_title}</span>
                </div>
                <div className="pitfall-severity">{pitfall.severity.toUpperCase()}</div>
              </div>

              <div className="pitfall-message">{pitfall.message}</div>

              <div className="pitfall-recommendation">
                <p className="recommendation-label">💡 How to fix:</p>
                <p>{pitfall.recommendation}</p>
              </div>

              {pitfall.affected_holdings.length > 0 && (
                <div className="affected-holdings">
                  <span className="holdings-label">Affected:</span>
                  <div className="holdings-list">
                    {pitfall.affected_holdings.map((ticker) => (
                      <span key={ticker} className="holding-badge">
                        {ticker}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <a href="#learn" className="learn-more-link">
                Learn more about this pitfall →
              </a>
            </div>
          ))}
        </div>
      )}

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <div className="recommendations-section">
          <h4>📋 Recommendations</h4>
          <ul className="recommendations-list">
            {recommendations.map((rec, idx) => (
              <li key={idx}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

      {pitfalls.length === 0 && (
        <div className="no-pitfalls">
          <p>✅ No major issues detected! Your portfolio looks well-diversified.</p>
        </div>
      )}
    </div>
  )
}

export default PitfallDetector
