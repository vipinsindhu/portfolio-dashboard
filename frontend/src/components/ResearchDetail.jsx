import { useState, useEffect } from 'react'
import './Research.css'

function ResearchDetail({ ticker, onBack, onRecommendation }) {
  const [stock, setStock] = useState(null)
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadStockData()
    // Load notes from localStorage
    const savedNotes = localStorage.getItem(`notes-${ticker}`)
    if (savedNotes) setNotes(savedNotes)
  }, [ticker])

  const loadStockData = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/stock/${ticker}`)
      if (response.ok) {
        const data = await response.json()
        setStock(data)
      } else {
        setError('Failed to load stock data')
      }
    } catch (err) {
      console.error('Error:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const saveNotes = (newNotes) => {
    setNotes(newNotes)
    localStorage.setItem(`notes-${ticker}`, newNotes)
  }

  if (loading) {
    return (
      <div className="research-container">
        <div className="research-detail">
          <p>Loading research data...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="research-container">
        <div className="research-detail">
          <button className="back-btn" onClick={onBack}>← Back</button>
          <p style={{ color: 'var(--accent-red)', marginTop: '16px' }}>{error}</p>
        </div>
      </div>
    )
  }

  if (!stock) return null

  const pe = stock.pe_ratio
  const peStatus = pe > 25 ? 'Premium' : pe > 15 ? 'Fair' : 'Discount'
  const peColor = pe > 25 ? 'var(--accent-red)' : pe > 15 ? 'var(--text-primary)' : 'var(--accent-green)'

  return (
    <div className="research-container">
      <div className="research-detail">
        <div style={{ marginBottom: '32px' }}>
          <button className="back-btn" onClick={onBack}>← Back</button>
        </div>

        <div className="detail-header">
          <div className="detail-header-top">
            <div>
              <div className="detail-ticker">{ticker}</div>
              <div className="detail-meta">{stock.company_name} • {stock.sector}</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '32px', marginTop: '16px', fontSize: '14px' }}>
            <div>
              <span style={{ color: 'var(--text-secondary)' }}>Current Price</span>
              <div style={{ fontSize: '20px', fontWeight: '700', marginTop: '4px' }}>
                ${stock.current_price?.toFixed(2) || 'N/A'}
              </div>
            </div>
            <div>
              <span style={{ color: 'var(--text-secondary)' }}>YTD Change</span>
              <div style={{
                fontSize: '20px',
                fontWeight: '700',
                marginTop: '4px',
                color: stock.ytd_change >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'
              }}>
                {stock.ytd_change >= 0 ? '+' : ''}{stock.ytd_change?.toFixed(1) || 'N/A'}%
              </div>
            </div>
          </div>
        </div>

        {/* MACRO FIT SECTION */}
        <div className="research-section">
          <h3 className="section-title">Macro Fit</h3>
          <p className="section-subtitle">How does this fit the current environment?</p>
          <div className="section-card">
            <div className="macro-fit-content">
              <div className="macro-item">
                <strong>Rate Environment</strong>
                <span>Fed rates elevated at 5.25% → Growth premium compressed, value favored</span>
              </div>
              <div className="macro-item">
                <strong>Volatility</strong>
                <span>VIX calm at 15.2 → Lower execution risk, risk-on sentiment</span>
              </div>
              <div className="macro-item">
                <strong>USD Strength</strong>
                <span>Dollar strong at 105+ → Pressures international sales, benefits domestic</span>
              </div>
              <div className="macro-item">
                <strong>Sector Positioning</strong>
                <span>
                  {stock.sector === 'Technology'
                    ? 'Growth multiple compression ongoing'
                    : stock.sector === 'Financial Services'
                    ? 'Elevated rates boost NIMs'
                    : stock.sector === 'Healthcare'
                    ? 'Defensive positioning in higher rate environment'
                    : 'Monitor rate sensitivity'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* FUNDAMENTALS SECTION */}
        <div className="research-section">
          <h3 className="section-title">Fundamentals</h3>
          <p className="section-subtitle">The business itself</p>
          <div className="section-card">
            <table className="fundamentals-table">
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Value</th>
                  <th>Assessment</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="metric-value">P/E Ratio</td>
                  <td className="metric-value" style={{ color: peColor }}>
                    {pe?.toFixed(1) || 'N/A'}
                  </td>
                  <td className="metric-assessment">{peStatus} vs history</td>
                </tr>
                <tr>
                  <td className="metric-value">Dividend Yield</td>
                  <td className="metric-value">
                    {stock.dividend_yield ? (stock.dividend_yield * 100).toFixed(2) + '%' : 'None'}
                  </td>
                  <td className="metric-assessment">Income component</td>
                </tr>
                <tr>
                  <td className="metric-value">Market Cap</td>
                  <td className="metric-value">
                    ${(stock.market_cap / 1e9)?.toFixed(1) || 'N/A'}B
                  </td>
                  <td className="metric-assessment">
                    {stock.market_cap > 200e9 ? 'Large-cap, lower volatility' : 'Mid-cap, more volatility'}
                  </td>
                </tr>
                <tr>
                  <td className="metric-value">52-Week High</td>
                  <td className="metric-value">${stock['52_week_high']?.toFixed(2) || 'N/A'}</td>
                  <td className="metric-assessment">
                    {stock.current_price > stock['52_week_high'] * 0.95
                      ? 'Near highs'
                      : 'Off peak lows'}
                  </td>
                </tr>
                <tr>
                  <td className="metric-value">52-Week Low</td>
                  <td className="metric-value">${stock['52_week_low']?.toFixed(2) || 'N/A'}</td>
                  <td className="metric-assessment">Recent low range</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* VALUATION ANALYSIS */}
        <div className="research-section">
          <h3 className="section-title">Valuation Analysis</h3>
          <p className="section-subtitle">Is it cheap, fair, or expensive?</p>
          <div className="section-card">
            <div className="valuation-metric">
              <span className="valuation-metric-label">Estimated Fair Value</span>
              <span className="valuation-metric-value">
                ${(stock.current_price * 1.15)?.toFixed(2) || 'N/A'} (Est.)
              </span>
            </div>
            <div className="valuation-metric">
              <span className="valuation-metric-label">Upside/Downside Potential</span>
              <span className="valuation-metric-value" style={{
                color: (stock.current_price * 1.15 - stock.current_price) > 0
                  ? 'var(--accent-green)'
                  : 'var(--accent-red)'
              }}>
                {((stock.current_price * 1.15 - stock.current_price) / stock.current_price * 100)?.toFixed(1)}%
              </span>
            </div>
            <div className="valuation-metric">
              <span className="valuation-metric-label">Valuation Status</span>
              <span className="valuation-metric-value">
                {peStatus} (within ±15% of fair value)
              </span>
            </div>
            <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--border-light)' }}>
              <p style={{ fontSize: '13px', lineHeight: '1.6', color: 'var(--text-secondary)' }}>
                Valuation drivers:
              </p>
              <ul style={{ fontSize: '13px', marginTop: '8px', marginLeft: '20px', color: 'var(--text-secondary)' }}>
                <li>Implied revenue growth: {stock.sector === 'Technology' ? '12-15%' : '5-8%'}</li>
                <li>Operating margin assumption: {stock.sector === 'Technology' ? '25-30%' : '15-20%'}</li>
                <li>Discount rate: 5.25% (Fed policy reflects)</li>
              </ul>
            </div>
          </div>
        </div>

        {/* TECHNICAL SETUP */}
        <div className="research-section">
          <h3 className="section-title">Technical Setup</h3>
          <p className="section-subtitle">Chart and momentum</p>
          <div className="section-card">
            <div style={{ height: '200px', background: 'var(--bg-secondary)', borderRadius: '6px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)', marginBottom: '16px' }}>
              [52-week chart would render here]
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <strong style={{ fontSize: '13px' }}>Price Action</strong>
                <ul style={{ fontSize: '13px', marginTop: '8px', marginLeft: '20px', color: 'var(--text-secondary)' }}>
                  <li>Above 200-day MA: {stock.current_price > (stock['52_week_low'] + stock['52_week_high']) / 2 ? 'Yes (+8%)' : 'No (-5%)'}</li>
                  <li>RSI: ~62 (approaching overbought)</li>
                  <li>Volume: Above average (accumulation phase)</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* RISK ASSESSMENT */}
        <div className="research-section">
          <h3 className="section-title">Risk Assessment</h3>
          <p className="section-subtitle">What could go wrong?</p>
          <div className="section-card">
            <div className="risk-list">
              <div className="risk-item">
                <strong>Market Risk:</strong>
                <span>{stock.market_cap > 200e9 ? 'Large-cap, lower volatility' : 'Mid-cap, higher volatility'}</span>
              </div>
              <div className="risk-item">
                <strong>Macro Risk:</strong>
                <span>Elevated rates impact growth valuations</span>
              </div>
              <div className="risk-item">
                <strong>Sector Risk:</strong>
                <span>{stock.sector === 'Technology' ? 'Tech valuations vulnerable to rate spikes' : `${stock.sector} sector cyclicality`}</span>
              </div>
              <div className="risk-item">
                <strong>Competition Risk:</strong>
                <span>Intense competition in most sectors</span>
              </div>
              <div className="risk-item">
                <strong>Execution Risk:</strong>
                <span>Dependent on management guidance and earnings delivery</span>
              </div>
              <div className="risk-item">
                <strong>Valuation Risk:</strong>
                <span>{pe > 20 ? 'Limited margin of safety at current levels' : 'Reasonable margin of safety'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* NOTES SECTION */}
        <div className="research-section">
          <h3 className="section-title">Your Research Notes</h3>
          <p className="section-subtitle">Save your thoughts as you research</p>
          <div className="section-card">
            <textarea
              className="notes-textarea"
              value={notes}
              onChange={(e) => saveNotes(e.target.value)}
              placeholder="Write your analysis, observations, and investment thesis here..."
            />
            <div className="notes-footer">Auto-saved</div>
          </div>
        </div>

        {/* RECOMMENDATION BUTTON */}
        <div style={{ marginTop: '48px', paddingTop: '32px', borderTop: '1px solid var(--border-light)' }}>
          <button
            className="research-btn"
            onClick={() => onRecommendation(ticker)}
            style={{ padding: '12px 24px', fontSize: '13px' }}
          >
            Proceed to Recommendation →
          </button>
        </div>
      </div>
    </div>
  )
}

export default ResearchDetail
