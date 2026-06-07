import { useState, useEffect } from 'react'
import './MacroAnalysis.css'

function MacroAnalysis() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    fetchAnalysis()
  }, [])

  const fetchAnalysis = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/macro-analysis')
      if (!response.ok) throw new Error('Failed to fetch macro analysis')
      const result = await response.json()
      setData(result)
      setError(null)
    } catch (err) {
      setError(err.message)
      console.error('Error fetching macro analysis:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRefresh = async () => {
    try {
      setRefreshing(true)
      const response = await fetch('/api/refresh-analysis', { method: 'POST' })
      if (!response.ok) throw new Error('Failed to refresh analysis')
      await fetchAnalysis()
    } catch (err) {
      setError(err.message)
      console.error('Error refreshing analysis:', err)
    } finally {
      setRefreshing(false)
    }
  }

  const getSignalColor = (signal) => {
    if (signal === 1) return '#34d399' // Green - tailwind
    if (signal === -1) return '#ef4444' // Red - headwind
    return '#9ca3af' // Gray - neutral
  }

  if (loading) {
    return <div className="macro-analysis-container"><p>Loading macro analysis...</p></div>
  }

  if (error) {
    return <div className="macro-analysis-container"><p className="error">Error: {error}</p></div>
  }

  const { macro_signals = {}, fund_impact = {}, forecasts = {}, metadata = {} } = data || {}

  return (
    <div className="macro-analysis-container">
      <div className="macro-header">
        <h2>Macro Analysis Dashboard</h2>
        <div className="header-controls">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="refresh-btn"
          >
            {refreshing ? 'Updating...' : 'Refresh Analysis'}
          </button>
          {metadata.last_updated && (
            <span className="last-updated">
              Last updated: {new Date(metadata.last_updated).toLocaleString()}
            </span>
          )}
        </div>
      </div>

      {/* Macro Signals Section */}
      <div className="analysis-section">
        <h3>9 Key Macro Indicators</h3>
        <div className="signals-grid">
          {Object.entries(macro_signals).map(([key, signal]) => (
            <div key={key} className="signal-card">
              <div className="signal-header">
                <h4>{signal.label}</h4>
                <span
                  className="signal-badge"
                  style={{ backgroundColor: getSignalColor(signal.signal) }}
                >
                  {signal.signal > 0 ? '📈' : signal.signal < 0 ? '📉' : '⏸️'}
                </span>
              </div>
              <p className="signal-value">{signal.value}</p>
              <p className="signal-context">{signal.context}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Fund Impact Section */}
      <div className="analysis-section">
        <h3>Per-Fund Macro Impact</h3>
        <div className="impact-grid">
          {Object.entries(fund_impact).map(([ticker, impact]) => (
            <div key={ticker} className="impact-card">
              <h4>{ticker}</h4>
              <div className="impact-score">
                <span className={`score ${impact.net_score > 0 ? 'positive' : impact.net_score < 0 ? 'negative' : 'neutral'}`}>
                  {impact.net_score > 0 ? '+' : ''}{impact.net_score}
                </span>
              </div>
              <p className="impact-detail">
                {impact.net_score > 0 && '✅ Net tailwind'}
                {impact.net_score < 0 && '⚠️ Net headwind'}
                {impact.net_score === 0 && '⏸️ Neutral'}
              </p>
              <div className="impact-breakdown">
                {Object.entries(impact.impact).map(([signal, value]) => (
                  <span
                    key={signal}
                    className="impact-badge"
                    title={signal}
                  >
                    {value > 0 ? '↑' : value < 0 ? '↓' : '→'}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Fund Forecasts Section */}
      <div className="analysis-section">
        <h3>3-5 Year Forecasts</h3>
        <div className="forecasts-grid">
          {Object.entries(forecasts).map(([ticker, forecast]) => (
            <div key={ticker} className="forecast-card">
              <div className="forecast-header">
                <h4>{ticker}</h4>
                <span
                  className="outlook-badge"
                  style={{ backgroundColor: forecast.color }}
                >
                  {forecast.outlook}
                </span>
              </div>

              <p className="forecast-scenario">{forecast.scenario}</p>

              <div className="forecast-body">
                <p><strong>Driver:</strong> {forecast.driver}</p>
                <p><strong>Risk:</strong> {forecast.risk}</p>
              </div>

              {forecast.current_price && (
                <div className="forecast-price">
                  <p>Current Price: ${forecast.current_price.toFixed(2)}</p>
                  {forecast.shares && (
                    <p>Shares: {forecast.shares.toFixed(4)}</p>
                  )}
                  {forecast.cost_basis && (
                    <p>Cost Basis: ${forecast.cost_basis.toFixed(2)}</p>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default MacroAnalysis
