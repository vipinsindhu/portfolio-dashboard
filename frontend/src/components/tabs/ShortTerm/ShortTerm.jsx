import { useState, useEffect } from 'react'
import SignalCard from '../../shared/SignalCard'
import './ShortTerm.css'

function ShortTerm() {
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
      const signalsResponse = await fetch('/api/signals/short-term')
      if (!signalsResponse.ok) throw new Error('Failed to fetch signals')
      const signalsData = await signalsResponse.json()
      setSignals(signalsData.signals || [])

      // Try to fetch portfolio recommendations
      try {
        const recsResponse = await fetch(
          '/api/portfolio/recommendations?timeframe=short_term'
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
    return <div className="short-term-container loading">Loading signals...</div>
  }

  return (
    <div className="short-term-container">
      <div className="short-term-header">
        <h2>📈 Quick Ideas (Next 1-3 Months)</h2>
        <p>Stocks to watch for quick moves based on recent news</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Portfolio-based Recommendations */}
      {hasPortfolio && recommendations && (
        <>
          {/* Sell/Reduce */}
          {recommendations.sell_reduce?.length > 0 && (
            <section className="signals-section sell-reduce">
              <h3 className="section-title">🔴 Sell/Reduce</h3>
              <p className="section-description">
                These holdings may be due for profit-taking in the current market
              </p>
              <div className="signals-grid">
                {recommendations.sell_reduce.map((signal, idx) => (
                  <SignalCard
                    key={idx}
                    signal={signal}
                    type="sell-reduce"
                    weight={signal.weight_in_portfolio}
                  />
                ))}
              </div>
            </section>
          )}

          {/* Hold */}
          {recommendations.hold?.length > 0 && (
            <section className="signals-section hold">
              <h3 className="section-title">⏸️ Hold</h3>
              <p className="section-description">
                Maintain positions; no action needed for these holdings
              </p>
              <div className="signals-grid">
                {recommendations.hold.map((signal, idx) => (
                  <SignalCard key={idx} signal={signal} type="hold" weight={signal.weight_in_portfolio} />
                ))}
              </div>
            </section>
          )}

          {/* Add */}
          {recommendations.add?.length > 0 && (
            <section className="signals-section add">
              <h3 className="section-title">🟢 Add/New Positions</h3>
              <p className="section-description">
                These would complement your current portfolio
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
          <h3 className="section-title">📊 Current Signals</h3>
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
          <p>No signals available at this time</p>
        </div>
      )}

      {/* Call to Action */}
      {!hasPortfolio && (
        <div className="cta-section">
          <div className="cta-content">
            <h4>Want personalized recommendations?</h4>
            <p>Upload your portfolio in the Analyse tab to get tailored short-term opportunities</p>
            <a href="#" className="btn-primary">
              Go to Analyse Tab
            </a>
          </div>
        </div>
      )}
    </div>
  )
}

export default ShortTerm
