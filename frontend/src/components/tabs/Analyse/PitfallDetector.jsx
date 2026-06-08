import { useState } from 'react'
import './PitfallDetector.css'

function PitfallDetector({ analysis }) {
  const [expandedSector, setExpandedSector] = useState(null)

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
          <div className="metric-label">Biggest Stock</div>
          <div className="metric-value">
            {(risk_metrics.largest_position_pct * 100).toFixed(1)}%
          </div>
          <div className="metric-hint">Keep under 15% (avoid too much risk)</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Top 3 Stocks Combined</div>
          <div className="metric-value">
            {(risk_metrics.top_3_concentration * 100).toFixed(1)}%
          </div>
          <div className="metric-hint">Keep under 50% (good mix)</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Number of Stocks</div>
          <div className="metric-value">{risk_metrics.holding_count}</div>
          <div className="metric-hint">Aim for 15-30 stocks</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Total Invested</div>
          <div className="metric-value">${(risk_metrics.total_value / 1000).toFixed(1)}k</div>
          <div className="metric-hint">Your total money in stocks</div>
        </div>
      </div>

      {/* Sector Allocation */}
      <div className="sector-section">
        <h4>Spread Across Industries</h4>
        <p className="sector-hint">See how your stocks spread across different industries. A good mix reduces risk.</p>
        <div className="sector-list">
          {Object.entries(sector_allocation)
            .sort((a, b) => b[1].current - a[1].current)
            .map(([sector, data]) => (
              <div key={sector} className={`sector-item sector-${data.status}`}>
                <div className="sector-header">
                  <div className="sector-name">
                    <span className="sector-status-badge">{data.status.toUpperCase()}</span>
                    {sector}
                  </div>
                  <div className="sector-values">
                    <span className="current">
                      <strong>{(data.current * 100).toFixed(1)}%</strong> current
                    </span>
                    <span className="target">
                      {(data.target * 100).toFixed(0)}% target
                    </span>
                  </div>
                </div>

                <div className="sector-bar-container">
                  <div className="bar-background">
                    {/* Target range indicator */}
                    <div
                      className="target-range"
                      style={{
                        left: `${data.min * 100}%`,
                        right: `${100 - data.max * 100}%`
                      }}
                    ></div>
                    {/* Current allocation bar */}
                    <div
                      className="sector-bar"
                      style={{ width: `${data.current * 100}%` }}
                    ></div>
                  </div>
                </div>

                <div className="sector-recommendation">{data.recommendation}</div>

                {/* Contributing Stocks */}
                {data.holdings && data.holdings.length > 0 && (
                  <div className="sector-holdings">
                    <button
                      type="button"
                      className="holdings-toggle"
                      onClick={() =>
                        setExpandedSector(expandedSector === sector ? null : sector)
                      }
                    >
                      <span className="toggle-arrow">
                        {expandedSector === sector ? '▼' : '▶'}
                      </span>
                      <span className="toggle-label">
                        Contributing Stocks ({data.holdings.length})
                      </span>
                    </button>

                    {expandedSector === sector && (
                      <div className="holdings-list">
                        {data.holdings.map((holding) => (
                          <div key={holding.symbol} className="holding-row">
                            <span className="holding-symbol">{holding.symbol}</span>
                            <span className="holding-percentage">
                              {holding.percentage.toFixed(1)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
        </div>
      </div>

      {/* Pitfalls */}
      {pitfalls.length > 0 && (
        <div className="pitfalls-section">
          <h4>⚠️ Things to Watch Out For</h4>

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
                <p className="recommendation-label">💡 What to do:</p>
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
          <h4>📋 Ideas to Improve</h4>
          <ul className="recommendations-list">
            {recommendations.map((rec, idx) => (
              <li key={idx}>{rec}</li>
            ))}
          </ul>
        </div>
      )}

      {pitfalls.length === 0 && (
        <div className="no-pitfalls">
          <p>Great job! Your portfolio looks balanced and well-spread across different investments.</p>
        </div>
      )}
    </div>
  )
}

export default PitfallDetector
