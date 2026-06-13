import { useState, useEffect } from 'react'
import './Welcome.css'

function Welcome({ onTabChange }) {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    fetch('/api/stats')
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setStats(data) })
      .catch(() => {})
  }, [])

  return (
    <div className="welcome-container">
      <section className="welcome-hero">
        <div className="hero-content">
          <h1 className="hero-title">Smart Stock Ideas</h1>
          <p className="hero-subtitle">AI-powered investment guidance for smarter portfolio decisions</p>
        </div>
        <div className="hero-ctas">
          <button className="btn-primary btn-large" onClick={() => onTabChange('short-term')}>
            Get Stock Ideas This Week
          </button>
          <button className="btn-secondary btn-large" onClick={() => onTabChange('analyse')}>
            Analyse My Portfolio
          </button>
        </div>
      </section>

      <section className="how-it-works">
        <h2>Get Started in 3 Steps</h2>
        <div className="steps-container">
          <div className="step">
            <div className="step-number">1</div>
            <h4>Browse Ideas</h4>
            <p>Go to <strong>This Week</strong> for short-term picks or <strong>Build Wealth</strong> for long-term holdings</p>
          </div>
          <div className="step-arrow">→</div>
          <div className="step">
            <div className="step-number">2</div>
            <h4>Check Your Portfolio</h4>
            <p>Head to <strong>Analyse</strong> and upload a CSV or add your holdings manually</p>
          </div>
          <div className="step-arrow">→</div>
          <div className="step">
            <div className="step-number">3</div>
            <h4>Learn & Improve</h4>
            <p>Visit <strong>Learn</strong> for lessons on investing pitfalls tied to your portfolio</p>
          </div>
        </div>
      </section>

      <section className="stats-section">
        <div className="stat">
          <div className="stat-number">{stats ? stats.ticker_count : '—'}</div>
          <div className="stat-label">Stocks & ETFs</div>
          <div className="stat-detail">{stats ? `Across ${stats.sector_count}+ sectors` : 'Loading…'}</div>
        </div>
        <div className="stat">
          <div className="stat-number">{stats ? `${stats.sector_count}+` : '—'}</div>
          <div className="stat-label">Sectors</div>
          <div className="stat-detail">Diversified coverage</div>
        </div>
        <div className="stat">
          <div className="stat-number">24h</div>
          <div className="stat-label">Signal refresh</div>
          <div className="stat-detail">AI-generated daily</div>
        </div>
        <div className="stat">
          <div className="stat-number">100%</div>
          <div className="stat-label">Free</div>
          <div className="stat-detail">No sign-up required</div>
        </div>
      </section>
    </div>
  )
}

export default Welcome
