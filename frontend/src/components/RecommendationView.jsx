import { useState, useEffect } from 'react'
import './Research.css'

function RecommendationView({ ticker, onBack }) {
  const [decision, setDecision] = useState('hold')
  const [confidence, setConfidence] = useState(7)
  const [thesis, setThesis] = useState('')
  const [savedDecisions, setSavedDecisions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadSavedDecision()
  }, [ticker])

  const loadSavedDecision = () => {
    const saved = localStorage.getItem(`recommendation-${ticker}`)
    if (saved) {
      const data = JSON.parse(saved)
      setDecision(data.decision)
      setConfidence(data.confidence)
      setThesis(data.thesis)
    }
    setLoading(false)
  }

  const saveDecision = () => {
    const decisionObj = {
      ticker,
      decision,
      confidence,
      thesis,
      savedAt: new Date().toISOString()
    }
    localStorage.setItem(`recommendation-${ticker}`, JSON.stringify(decisionObj))

    // Add to history
    const history = JSON.parse(localStorage.getItem('recommendation-history') || '[]')
    const existing = history.findIndex(d => d.ticker === ticker && d.decision === decision)
    if (existing >= 0) {
      history.splice(existing, 1)
    }
    history.unshift(decisionObj)
    localStorage.setItem('recommendation-history', JSON.stringify(history.slice(0, 50)))
  }

  const decisionColor = decision === 'buy' ? 'var(--accent-green)' : decision === 'avoid' ? 'var(--accent-red)' : 'var(--accent-neutral)'
  const decisionLabel = decision === 'buy' ? 'BUY' : decision === 'avoid' ? 'AVOID' : 'HOLD'
  const decisionSubtext = decision === 'buy' ? 'Strong upside potential' : decision === 'avoid' ? "Don't buy yet" : "Monitor, not ready"

  return (
    <div className="research-container">
      <div className="recommendation-section">
        <div style={{ marginBottom: '32px' }}>
          <button className="back-btn" onClick={onBack}>← Back</button>
        </div>

        <div className="recommendation-header">
          <h1 className="recommendation-title">{ticker} Investment Decision</h1>
        </div>

        {/* DECISION BOX */}
        <div className="decision-box">
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Your Decision
          </p>
          <div className="decision-word" style={{ color: decisionColor }}>
            {decisionLabel}
          </div>
          <p className="decision-subtitle">{decisionSubtext}</p>

          <div className="confidence-group">
            <div className="confidence-item">
              <div className="confidence-label">Confidence</div>
              <div className="confidence-value">{confidence}/10</div>
            </div>
            <div className="confidence-item">
              <div className="confidence-label">Conviction</div>
              <div className="confidence-value">
                {confidence >= 8 ? 'High' : confidence >= 6 ? 'Moderate' : 'Low'}
              </div>
            </div>
          </div>

          <div style={{ marginTop: '24px', paddingTop: '24px', borderTop: '1px solid var(--border-light)' }}>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)', display: 'block', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Adjust Confidence
            </label>
            <input
              type="range"
              min="1"
              max="10"
              value={confidence}
              onChange={(e) => setConfidence(parseInt(e.target.value))}
              style={{
                width: '100%',
                height: '6px',
                borderRadius: '3px',
                outline: 'none',
                accentColor: decisionColor
              }}
            />
          </div>
        </div>

        {/* DECISION RATIONALE */}
        <div className="research-section">
          <h3 className="section-title">Decision Rationale</h3>

          <div className="pros-cons">
            <div className="pros-box">
              <div className="pros-cons-title">Pros (Why Consider)</div>
              <div className="pros-list">
                <div className="pro-item">Strong business fundamentals</div>
                <div className="pro-item">Reasonable valuation at current levels</div>
                <div className="pro-item">Sector positioned for growth</div>
              </div>
            </div>

            <div className="cons-box">
              <div className="pros-cons-title">Cons (Why Hold/Avoid)</div>
              <div className="cons-list">
                <div className="con-item">Limited margin of safety given macro</div>
                <div className="con-item">Already reflected in price</div>
                <div className="con-item">Execution risk on catalysts</div>
              </div>
            </div>
          </div>

          {decision === 'hold' && (
            <div style={{
              padding: '16px',
              background: 'var(--bg-light)',
              borderRadius: '6px',
              borderLeft: '4px solid var(--accent-neutral)',
              marginBottom: '24px'
            }}>
              <strong style={{ fontSize: '13px' }}>Better Entry Price</strong>
              <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Wait for pullback to $XXX (-7% from current) for better margin of safety
              </p>
            </div>
          )}
        </div>

        {/* ACTION ITEMS */}
        <div className="action-items">
          <div className="action-items-title">Action Items</div>
          <div className="action-list">
            <label className="action-item">
              <input type="checkbox" className="action-checkbox" defaultChecked />
              <span>Set price alert for entry level</span>
            </label>
            <label className="action-item">
              <input type="checkbox" className="action-checkbox" defaultChecked />
              <span>Monitor next earnings report</span>
            </label>
            <label className="action-item">
              <input type="checkbox" className="action-checkbox" />
              <span>Review if Fed policy shifts</span>
            </label>
            <label className="action-item">
              <input type="checkbox" className="action-checkbox" />
              <span>Reassess in 3 months</span>
            </label>
          </div>
        </div>

        {/* ALTERNATIVE SCENARIOS */}
        <div className="scenarios-box">
          <div className="scenarios-title">Alternative Scenarios</div>
          <div className="scenario-list">
            <div className="scenario-item">
              <div className="scenario-condition">IF Price drops 10%</div>
              <div className="scenario-outcome">→ UPGRADE to BUY (better margin of safety)</div>
            </div>
            <div className="scenario-item">
              <div className="scenario-condition">IF Fed cuts rates 1%</div>
              <div className="scenario-outcome">→ Upgrade conviction (valuation multiple expansion)</div>
            </div>
            <div className="scenario-item">
              <div className="scenario-condition">IF Earnings miss forecast</div>
              <div className="scenario-outcome">→ DOWNGRADE to AVOID (growth story broken)</div>
            </div>
          </div>
        </div>

        {/* INVESTMENT THESIS */}
        <div className="research-section">
          <h3 className="section-title">Your Investment Thesis</h3>
          <div className="section-card">
            <textarea
              className="notes-textarea"
              value={thesis}
              onChange={(e) => setThesis(e.target.value)}
              placeholder="Summarize your investment thesis, key thesis drivers, and conviction level..."
            />
          </div>
        </div>

        {/* BUTTONS */}
        <div style={{
          display: 'flex',
          gap: '12px',
          marginTop: '48px',
          paddingTop: '32px',
          borderTop: '1px solid var(--border-light)'
        }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input
                type="radio"
                name="decision"
                value="buy"
                checked={decision === 'buy'}
                onChange={(e) => setDecision(e.target.value)}
              />
              <span style={{ fontSize: '13px' }}>Buy</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input
                type="radio"
                name="decision"
                value="hold"
                checked={decision === 'hold'}
                onChange={(e) => setDecision(e.target.value)}
              />
              <span style={{ fontSize: '13px' }}>Hold</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input
                type="radio"
                name="decision"
                value="avoid"
                checked={decision === 'avoid'}
                onChange={(e) => setDecision(e.target.value)}
              />
              <span style={{ fontSize: '13px' }}>Avoid</span>
            </label>
          </div>

          <button
            className="research-btn"
            onClick={() => {
              saveDecision()
              alert(`${ticker} ${decisionLabel} decision saved!`)
            }}
            style={{ padding: '10px 20px', marginLeft: 'auto' }}
          >
            Save Decision
          </button>
        </div>
      </div>
    </div>
  )
}

export default RecommendationView
