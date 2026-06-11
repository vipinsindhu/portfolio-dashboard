import { useState } from 'react'
import './Welcome.css'

function Welcome({ onTabChange, onFeedback, onTryDemo }) {
  const [hoveredFeature, setHoveredFeature] = useState(null)

  return (
    <div className="welcome-container">
      {/* Hero Section */}
      <section className="welcome-hero">
        <div className="hero-content">
          <h1 className="hero-title">📊 Smart Stock Ideas</h1>
          <p className="hero-subtitle">
            AI-powered investment guidance for smarter portfolio decisions
          </p>
          <p className="hero-description">
            Get intelligent stock recommendations, analyze your portfolio for risks, and learn to invest like the pros.
          </p>
        </div>

        {/* CTA Buttons */}
        <div className="hero-ctas">
          <button
            className="btn-primary btn-large"
            onClick={() => onTabChange('short-term')}
          >
            🚀 Get Stock Ideas This Week
          </button>
          <button
            className="btn-secondary btn-large"
            onClick={() => onTabChange('analyse')}
          >
            📊 Analyze My Portfolio
          </button>
          <button
            className="btn-secondary btn-large"
            onClick={onTryDemo}
          >
            ✨ Try a Demo
          </button>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <h2>Why Use Smart Stock Ideas?</h2>
        <p className="section-subtitle">Everything you need to invest with confidence</p>

        <div className="features-grid">
          {/* Feature 1 */}
          <div
            className={`feature-card ${hoveredFeature === 1 ? 'active' : ''}`}
            onMouseEnter={() => setHoveredFeature(1)}
            onMouseLeave={() => setHoveredFeature(null)}
          >
            <div className="feature-icon">💡</div>
            <h3>AI Stock Picks</h3>
            <p>Get intelligent recommendations for this week's best opportunities and long-term wealth builders.</p>
            <div className="feature-highlight">Updated every hour</div>
          </div>

          {/* Feature 2 */}
          <div
            className={`feature-card ${hoveredFeature === 2 ? 'active' : ''}`}
            onMouseEnter={() => setHoveredFeature(2)}
            onMouseLeave={() => setHoveredFeature(null)}
          >
            <div className="feature-icon">⚠️</div>
            <h3>Portfolio Risk Check</h3>
            <p>Upload your stocks and get instant analysis: concentration risks, sector balance, and diversification issues.</p>
            <div className="feature-highlight">CSV or manual entry</div>
          </div>

          {/* Feature 3 */}
          <div
            className={`feature-card ${hoveredFeature === 3 ? 'active' : ''}`}
            onMouseEnter={() => setHoveredFeature(3)}
            onMouseLeave={() => setHoveredFeature(null)}
          >
            <div className="feature-icon">📚</div>
            <h3>Investment Education</h3>
            <p>Learn from real portfolio issues. Get lessons on diversification, concentration, and investing mistakes.</p>
            <div className="feature-highlight">Personalized to your portfolio</div>
          </div>

          {/* Feature 4 */}
          <div
            className={`feature-card ${hoveredFeature === 4 ? 'active' : ''}`}
            onMouseEnter={() => setHoveredFeature(4)}
            onMouseLeave={() => setHoveredFeature(null)}
          >
            <div className="feature-icon">🎯</div>
            <h3>Two Timeframes</h3>
            <p>Short-term trading picks for this week OR long-term wealth building picks to hold for years.</p>
            <div className="feature-highlight">Pick your style</div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="how-it-works">
        <h2>Get Started in 3 Steps</h2>

        <div className="steps-container">
          <div className="step">
            <div className="step-number">1</div>
            <h4>Browse Ideas</h4>
            <p>
              Go to <strong>"This Week"</strong> for short-term picks or{' '}
              <strong>"Build Wealth"</strong> for long-term holdings
            </p>
          </div>

          <div className="step-arrow">→</div>

          <div className="step">
            <div className="step-number">2</div>
            <h4>Analyze Your Portfolio</h4>
            <p>
              Head to <strong>"My Stocks"</strong> and upload a CSV or add your holdings manually
            </p>
          </div>

          <div className="step-arrow">→</div>

          <div className="step">
            <div className="step-number">3</div>
            <h4>Learn & Improve</h4>
            <p>
              Check the <strong>"Learn"</strong> tab for lessons on investing pitfalls tied to your portfolio
            </p>
          </div>
        </div>
      </section>

      {/* Key Stats Section */}
      <section className="stats-section">
        <div className="stat">
          <div className="stat-number">41</div>
          <div className="stat-label">Stocks & ETFs</div>
          <div className="stat-detail">Across 8+ sectors</div>
        </div>

        <div className="stat">
          <div className="stat-number">8+</div>
          <div className="stat-label">Sectors</div>
          <div className="stat-detail">Diversified coverage</div>
        </div>

        <div className="stat">
          <div className="stat-number">3 Signals</div>
          <div className="stat-label">Per Stock</div>
          <div className="stat-detail">Buy, Hold, or Avoid</div>
        </div>

        <div className="stat">
          <div className="stat-number">100%</div>
          <div className="stat-label">Free</div>
          <div className="stat-detail">No sign-up required</div>
        </div>
      </section>

      {/* Disclaimer */}
      <section className="disclaimer-section">
        <div className="disclaimer-box">
          <strong>⚠️ Important Disclaimer</strong>
          <p>
            This app uses AI to generate stock recommendations and is NOT financial advice. Always do your own research,
            consult a licensed financial advisor, and only invest money you can afford to lose. Past performance doesn't
            guarantee future results.
          </p>
        </div>
      </section>

      {/* Feedback CTA */}
      <section className="feedback-cta-section">
        <div className="feedback-box">
          <h3>Help Us Improve! 💬</h3>
          <p>Your feedback makes this app better for everyone. Found a bug? Have a feature idea? Let us know!</p>
          <button className="btn-feedback-large" onClick={onFeedback}>
            💬 Send Feedback
          </button>
        </div>
      </section>

      {/* Final CTA */}
      <section className="final-cta">
        <h2>Ready to get smarter about your stocks?</h2>
        <div className="final-cta-buttons">
          <button className="btn-primary btn-large" onClick={() => onTabChange('short-term')}>
            🚀 Start Exploring Ideas
          </button>
          <button className="btn-secondary btn-large" onClick={() => onTabChange('analyse')}>
            📊 Upload Your Portfolio
          </button>
        </div>
      </section>
    </div>
  )
}

export default Welcome
