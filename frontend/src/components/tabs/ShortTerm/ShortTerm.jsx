import { useState, useEffect } from 'react'
import SignalCard from '../../shared/SignalCard'
import RecommendationStats from './RecommendationStats'
import FilterBar from './FilterBar'
import SignalCardEnhanced from './SignalCardEnhanced'
import './ShortTerm.css'

function ShortTerm() {
  const [signals, setSignals] = useState([])
  const [filteredSignals, setFilteredSignals] = useState([])
  const [stats, setStats] = useState(null)
  const [generatedAt, setGeneratedAt] = useState(null)
  const [recommendations, setRecommendations] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [hasPortfolio, setHasPortfolio] = useState(false)
  const [filters, setFilters] = useState({
    direction: 'all',
    min_confidence: 6,
    sector: null
  })

  useEffect(() => {
    fetchData()

    // Auto-refresh every 60 minutes (3600000 ms) to match signal generation frequency
    const refreshInterval = setInterval(() => {
      console.log('Auto-refreshing signals (60-minute cycle)')
      fetchData()
    }, 3600000)

    return () => clearInterval(refreshInterval)
  }, [])

  const fetchData = async () => {
    setLoading(true)
    setError(null)

    try {
      // Fetch signals with current filters
      const params = new URLSearchParams()
      if (filters.direction !== 'all') params.append('direction', filters.direction)
      if (filters.min_confidence !== 6) params.append('min_confidence', filters.min_confidence)
      if (filters.sector) params.append('sector', filters.sector)

      const signalsResponse = await fetch(`/api/signals/short-term?${params.toString()}`)
      if (!signalsResponse.ok) throw new Error('Failed to fetch signals')
      const signalsData = await signalsResponse.json()

      setSignals(signalsData.signals || [])
      setFilteredSignals(signalsData.signals || [])
      setStats(signalsData.stats)
      setGeneratedAt(signalsData.generated_at)

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

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters)
    // Refetch with new filters
    setLoading(true)
    fetchDataWithFilters(newFilters)
  }

  const fetchDataWithFilters = async (filters) => {
    setError(null)
    try {
      const params = new URLSearchParams()
      if (filters.direction !== 'all') params.append('direction', filters.direction)
      if (filters.min_confidence !== 6) params.append('min_confidence', filters.min_confidence)
      if (filters.sector) params.append('sector', filters.sector)

      const response = await fetch(`/api/signals/short-term?${params.toString()}`)
      if (!response.ok) throw new Error('Failed to fetch signals')
      const data = await response.json()

      setSignals(data.signals || [])
      setFilteredSignals(data.signals || [])
      setStats(data.stats)
      setGeneratedAt(data.generated_at)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading && signals.length === 0) {
    return (
      <div className="short-term-container loading">
        <div className="loading-spinner">⏳ Loading signals...</div>
      </div>
    )
  }

  return (
    <div className="short-term-container">
      <div className="short-term-header">
        <div className="header-top">
          <div>
            <h2>💡 Stock Ideas for This Week</h2>
            <p>AI picked these stocks based on what's happening in the markets right now</p>
          </div>
          <button
            className="btn-refresh"
            onClick={() => {
              setLoading(true)
              fetchData()
            }}
            disabled={loading}
            title="Refresh signals manually"
          >
            {loading ? '⏳ Refreshing...' : '🔄 Refresh'}
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Stats Display */}
      {stats && <RecommendationStats stats={stats} generatedAt={generatedAt} />}

      {/* Filters */}
      {signals.length > 0 && (
        <FilterBar onFilterChange={handleFilterChange} stats={stats} />
      )}

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

      {/* Top Signals (General or Filtered) */}
      {filteredSignals.length > 0 && (
        <>
          {/* Buy Signals */}
          {filteredSignals.filter(s => s.direction === 'buy').length > 0 && (
            <section className="signals-section buy">
              <h3 className="section-title">🟢 Good Time to Buy</h3>
              <p className="section-description">
                These stocks look like good buys right now
              </p>
              <div className="signals-grid">
                {filteredSignals
                  .filter(s => s.direction === 'buy')
                  .map((signal, idx) => (
                    <SignalCardEnhanced key={idx} signal={signal} type="buy" />
                  ))}
              </div>
            </section>
          )}

          {/* Hold Signals */}
          {filteredSignals.filter(s => s.direction === 'hold').length > 0 && (
            <section className="signals-section hold">
              <h3 className="section-title">⏸️ Wait and See</h3>
              <p className="section-description">
                These could be good, but wait a bit longer to decide
              </p>
              <div className="signals-grid">
                {filteredSignals
                  .filter(s => s.direction === 'hold')
                  .map((signal, idx) => (
                    <SignalCardEnhanced key={idx} signal={signal} type="hold" />
                  ))}
              </div>
            </section>
          )}

          {/* Avoid Signals */}
          {filteredSignals.filter(s => s.direction === 'avoid').length > 0 && (
            <section className="signals-section avoid">
              <h3 className="section-title">🔴 Skip These</h3>
              <p className="section-description">
                These stocks might not be good buys right now
              </p>
              <div className="signals-grid">
                {filteredSignals
                  .filter(s => s.direction === 'avoid')
                  .map((signal, idx) => (
                    <SignalCardEnhanced key={idx} signal={signal} type="avoid" />
                  ))}
              </div>
            </section>
          )}
        </>
      )}

      {/* Empty State */}
      {filteredSignals.length === 0 && (
        <div className="empty-state">
          <p>😴 No ideas match your filters</p>
          <p className="empty-hint">Try changing your filters or check back later</p>
        </div>
      )}

      {/* Call to Action */}
      {!hasPortfolio && signals.length > 0 && (
        <div className="cta-section">
          <div className="cta-content">
            <h4>💼 Upload Your Stocks?</h4>
            <p>Tell us what you own, and we'll give you personalized ideas just for your portfolio</p>
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
