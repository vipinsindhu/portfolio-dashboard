import { useState, useEffect } from 'react'
import SignalCard from '../../shared/SignalCard'
import SignalCardEnhanced from '../ShortTerm/SignalCardEnhanced'
import FilterBar from '../ShortTerm/FilterBar'
import RecommendationStats from '../ShortTerm/RecommendationStats'
import { usePortfolioRecommendations } from '../../../hooks/usePortfolioRecommendations'
import './LongTerm.css'

function LongTerm() {
  const [signals, setSignals] = useState([])
  const [filteredSignals, setFilteredSignals] = useState([])
  const [stats, setStats] = useState(null)
  const [generatedAt, setGeneratedAt] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [hasPortfolio, setHasPortfolio] = useState(false)

  // Use cached portfolio recommendations hook (fallback if not in signals response)
  const { recommendations: hookRecommendations } = usePortfolioRecommendations('long_term')
  const [signalRecommendations, setSignalRecommendations] = useState(null)
  const [filters, setFilters] = useState({
    direction: 'all',
    min_confidence: 5,
    sector: null
  })

  // Use recommendations from signals response if available, otherwise fall back to hook
  const recommendations = signalRecommendations || hookRecommendations

  useEffect(() => {
    fetchData()

    // Auto-refresh every 60 minutes (3600000 ms) to match signal generation frequency
    const refreshInterval = setInterval(() => {
      console.log('Auto-refreshing long-term signals (60-minute cycle)')
      fetchData()
    }, 3600000)

    return () => clearInterval(refreshInterval)
  }, [])

  // Update hasPortfolio when recommendations load
  useEffect(() => {
    if (recommendations) {
      setHasPortfolio(true)
    }
  }, [recommendations])

  const fetchData = async () => {
    setLoading(true)
    setError(null)

    try {
      // Fetch signals with current filters
      const params = new URLSearchParams()
      if (filters.direction !== 'all') params.append('direction', filters.direction)
      if (filters.min_confidence !== 5) params.append('min_confidence', filters.min_confidence)
      if (filters.sector) params.append('sector', filters.sector)

      const signalsResponse = await fetch(`/api/signals/long-term?${params.toString()}`)
      if (!signalsResponse.ok) throw new Error('Failed to fetch signals')
      const signalsData = await signalsResponse.json()

      setSignals(signalsData.signals || [])
      setFilteredSignals(signalsData.signals || [])
      setStats(signalsData.stats)
      setGeneratedAt(signalsData.generated_at)

      // Use recommendations from signals response if available (combined API call)
      if (signalsData.recommendations) {
        setSignalRecommendations(signalsData.recommendations)
        setHasPortfolio(true)
      }

      // Check if recommendations are available (will be loaded by the hook)
      setHasPortfolio(!!recommendations)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters)
    // Apply filters client-side (no server call needed)
    applyFiltersClientSide(signals, newFilters)
  }

  const applyFiltersClientSide = (allSignals, filters) => {
    let filtered = allSignals

    // Filter by direction
    if (filters.direction && filters.direction !== 'all') {
      filtered = filtered.filter(s => s.direction === filters.direction)
    }

    // Filter by confidence
    if (filters.min_confidence) {
      filtered = filtered.filter(s => s.confidence >= filters.min_confidence)
    }

    // Filter by sector
    if (filters.sector) {
      filtered = filtered.filter(s => s.sector === filters.sector)
    }

    setFilteredSignals(filtered)
  }

  if (loading && signals.length === 0) {
    return (
      <div className="long-term-container loading">
        <div className="loading-spinner">⏳ Loading signals...</div>
      </div>
    )
  }

  return (
    <div className="long-term-container">
      <div className="long-term-header">
        <div className="header-top">
          <div>
            <h2>🎯 Build Wealth Long-term</h2>
            <p>Quality companies to hold for years</p>
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
          {/* Core Holdings */}
          {recommendations.hold?.length > 0 && (
            <section className="signals-section hold-section">
              <h3 className="section-title">🏢 Keep These</h3>
              <p className="section-description">
                Your best stocks - hold onto them
              </p>
              <div className="signals-grid">
                {recommendations.hold.map((signal, idx) => (
                  <SignalCard
                    key={idx}
                    signal={signal}
                    type="hold"
                  />
                ))}
              </div>
            </section>
          )}

          {/* Defensive Positions */}
          {recommendations.sell_reduce?.length > 0 && (
            <section className="signals-section defensive-section">
              <h3 className="section-title">🛡️ Consider Selling</h3>
              <p className="section-description">
                These might be worth reducing or removing
              </p>
              <div className="signals-grid">
                {recommendations.sell_reduce.map((signal, idx) => (
                  <SignalCard key={idx} signal={signal} type="sell-reduce" />
                ))}
              </div>
            </section>
          )}

          {/* New Opportunities */}
          {recommendations.add?.length > 0 && (
            <section className="signals-section opportunity-section">
              <h3 className="section-title">⭐ Add to Your Portfolio</h3>
              <p className="section-description">
                New stocks that would fit well with yours
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

      {/* Top Signals (General or Filtered) - Deduplicated */}
      {(() => {
        // Remove stocks already in portfolio recommendations from general signals
        const recommendationTickers = new Set()
        if (recommendations) {
          if (recommendations.sell_reduce) recommendations.sell_reduce.forEach(s => recommendationTickers.add(s.ticker))
          if (recommendations.hold) recommendations.hold.forEach(s => recommendationTickers.add(s.ticker))
          if (recommendations.add) recommendations.add.forEach(s => recommendationTickers.add(s.ticker))
        }

        const deduplicatedSignals = filteredSignals.filter(s => !recommendationTickers.has(s.ticker))
        return deduplicatedSignals.length > 0 ? (
        <>
          {/* Buy Signals */}
          {deduplicatedSignals.filter(s => s.direction === 'buy').length > 0 && (
            <section className="signals-section buy">
              <h3 className="section-title">🟢 Great Picks</h3>
              <p className="section-description">
                Quality companies to buy and hold
              </p>
              <div className="signals-grid">
                {deduplicatedSignals
                  .filter(s => s.direction === 'buy')
                  .map((signal, idx) => (
                    <SignalCardEnhanced key={idx} signal={signal} type="buy" />
                  ))}
              </div>
            </section>
          )}

          {/* Hold Signals */}
          {deduplicatedSignals.filter(s => s.direction === 'hold').length > 0 && (
            <section className="signals-section hold">
              <h3 className="section-title">⏸️ Hold for Now</h3>
              <p className="section-description">
                Good companies, but maybe wait for a better price
              </p>
              <div className="signals-grid">
                {deduplicatedSignals
                  .filter(s => s.direction === 'hold')
                  .map((signal, idx) => (
                    <SignalCardEnhanced key={idx} signal={signal} type="hold" />
                  ))}
              </div>
            </section>
          )}

          {/* Avoid Signals */}
          {deduplicatedSignals.filter(s => s.direction === 'avoid').length > 0 && (
            <section className="signals-section avoid">
              <h3 className="section-title">🔴 Skip These</h3>
              <p className="section-description">
                Not good picks right now
              </p>
              <div className="signals-grid">
                {deduplicatedSignals
                  .filter(s => s.direction === 'avoid')
                  .map((signal, idx) => (
                    <SignalCardEnhanced key={idx} signal={signal} type="avoid" />
                  ))}
              </div>
            </section>
          )}
        </>
        ) : null
      })()}

      {/* Empty State */}
      {filteredSignals.length === 0 && (
        <div className="empty-state">
          <p>😴 No signals match your filters</p>
          <p className="empty-hint">Try changing your filters or check back later</p>
        </div>
      )}

      {/* Call to Action for Portfolio Upload */}
      {!hasPortfolio && filteredSignals.length > 0 && (
        <div className="cta-section">
          <div className="cta-content">
            <h4>💼 Show Us Your Stocks?</h4>
            <p>Upload what you own, and we'll tell you which are good to keep and which to sell</p>
            <a href="#" className="btn-primary">
              Go to Analyse Tab
            </a>
          </div>
        </div>
      )}

      {/* Educational Section */}
      <div className="education-section">
        <div className="education-card">
          <h3>💡 Why Long-term Investing?</h3>
          <p>
            Patient investors make more money. Holding quality stocks for years beats trying to time the market.
            The best investors focus on good companies and keep them, ignoring short-term ups and downs.
          </p>
          <p>
            Use the filters to find stocks you're comfortable holding for years. The higher the confidence score, the better the stock looks for the long run.
          </p>
        </div>
      </div>
    </div>
  )
}

export default LongTerm
