import { useState, useEffect } from 'react'
import SignalCard from '../../shared/SignalCard'
import './LongTerm.css'

function LongTerm() {
  const [signals, setSignals] = useState([])
  const [recommendations, setRecommendations] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [hasPortfolio, setHasPortfolio] = useState(false)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    setError(null)

    try {
      // Fetch signals
      const signalsResponse = await fetch('/api/signals/long-term')
      if (!signalsResponse.ok) throw new Error('Failed to fetch signals')
      const signalsData = await signalsResponse.json()
      setSignals(signalsData.signals || [])

      // Try to fetch portfolio recommendations
      try {
        const recsResponse = await fetch(
          '/api/portfolio/recommendations?timeframe=long_term'
        )
        if (recsResponse.ok) {
          const recsData = await recsResponse.json()
          setRecommendations(recsData)
          setHasPortfolio(true)
        }
      } catch {
        setHasPortfolio(false)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="long-term-container loading">Loading signals...</div>
  }

  return (
    <div className="long-term-container">
      <div className="long-term-header">
        <h2>🎯 Long-term Strategy (1+ years)</h2>
        <p>Build wealth with fundamentals-focused holdings for buy-and-hold investors</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Investment Philosophy */}
      <div className="philosophy-section">
        <div className="philosophy-card">
          <h3>💡 Long-term Investing Principles</h3>
          <ul className="principles-list">
            <li>Focus on company fundamentals, not market noise</li>
            <li>Diversify across sectors and market caps</li>
            <li>Reinvest dividends for compound growth</li>
            <li>Rebalance annually to stay on track</li>
            <li>Ignore short-term volatility</li>
          </ul>
        </div>
      </div>

      {/* Portfolio-based Recommendations */}
      {hasPortfolio && recommendations && (
        <>
          {/* Core Holdings */}
          {recommendations.hold?.length > 0 && (
            <section className="signals-section hold-section">
              <h3 className="section-title">🏢 Core Holdings</h3>
              <p className="section-description">
                Strong fundamentals - maintain and possibly accumulate on dips
              </p>
              <div className="signals-grid">
                {recommendations.hold.map((signal, idx) => (
                  <SignalCard
                    key={idx}
                    signal={signal}
                    type="hold"
                    weight={signal.weight_in_portfolio}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Defensive Positions */}
          {recommendations.sell_reduce?.length > 0 && (
            <section className="signals-section defensive-section">
              <h3 className="section-title">🛡️ Defensive Positions</h3>
              <p className="section-description">
                Consider trimming or reviewing these holdings
              </p>
              <div className="signals-grid">
                {recommendations.sell_reduce.map((signal, idx) => (
                  <SignalCard key={idx} signal={signal} type="sell-reduce" weight={signal.weight_in_portfolio} />
                ))}
              </div>
            </section>
          )}

          {/* New Opportunities */}
          {recommendations.add?.length > 0 && (
            <section className="signals-section opportunity-section">
              <h3 className="section-title">⭐ New Opportunities</h3>
              <p className="section-description">
                Quality companies that complement your portfolio
              </p>
              <div className="signals-grid">
                {recommendations.add.map((signal, idx) => (
                  <SignalCard key={idx} signal={signal} type="add" />
                ))}
              </div>
            </section>
          )}
        </>
      )}

      {/* General Signals (no portfolio) */}
      {!hasPortfolio && signals.length > 0 && (
        <section className="signals-section general">
          <h3 className="section-title">📊 Quality Holdings for Long-term</h3>
          <p className="section-description">
            Upload your portfolio to get personalized recommendations
          </p>
          <div className="signals-grid">
            {signals.map((signal, idx) => (
              <SignalCard key={idx} signal={signal} />
            ))}
          </div>
        </section>
      )}

      {/* Empty State */}
      {signals.length === 0 && !recommendations && (
        <div className="empty-state">
          <p>No long-term signals available at this time</p>
        </div>
      )}

      {/* Educational Section */}
      <div className="education-section">
        <div className="education-card">
          <h3>📚 Why Long-term Investing?</h3>
          <p>
            History shows that long-term investors who buy quality companies and hold through market
            cycles outperform active traders by a wide margin. The average investor earns 10-11%
            annually in a diversified portfolio, while market timing reduces returns by 2-4%.
          </p>
          <p>
            Focus on companies with strong earnings growth, healthy balance sheets, and sustainable
            competitive advantages. Time in the market beats timing the market.
          </p>
        </div>
      </div>

      {/* Call to Action */}
      {!hasPortfolio && (
        <div className="cta-section">
          <div className="cta-content">
            <h4>Build your long-term portfolio</h4>
            <p>Upload your holdings to get personalized long-term recommendations</p>
            <a href="#" className="btn-primary">
              Go to Analyse Tab
            </a>
          </div>
        </div>
      )}
    </div>
  )
}

export default LongTerm
