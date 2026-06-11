import { useState, useEffect } from 'react'
import SignalCard from '../../shared/SignalCard'
import RecommendationStats from './RecommendationStats'
import FilterBar from './FilterBar'
import SignalCardEnhanced from './SignalCardEnhanced'
import { usePortfolioRecommendations } from '../../../hooks/usePortfolioRecommendations'
import './ShortTerm.css'

function ShortTerm() {
  const [signals, setSignals] = useState([])
  const [filteredSignals, setFilteredSignals] = useState([])
  const [stats, setStats] = useState(null)
  const [generatedAt, setGeneratedAt] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [hasPortfolio, setHasPortfolio] = useState(false)

  // Use cached portfolio recommendations hook (fallback if not in signals response)
  const { recommendations: hookRecommendations } = usePortfolioRecommendations('short_term')
  const [signalRecommendations, setSignalRecommendations] = useState(null)
  const [filters, setFilters] = useState({
    direction: 'all',
    min_confidence: 6,
    sector: null
  })

  // Use recommendations from signals response if available, otherwise fall back to hook
  const recommendations = signalRecommendations || hookRecommendations

  useEffect(() => {
    fetchData()

    // Auto-refresh every 60 minutes (3600000 ms) to match signal generation frequency
    const refreshInterval = setInterval(() => {
      console.log('Auto-refreshing signals (60-minute cycle)')
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
      if (filters.min_confidence !== 6) params.append('min_confidence', filters.min_confidence)
      if (filters.sector) params.append('sector', filters.sector)

      const signalsResponse = await fetch(`/api/signals/short-term?${params.toString()}`)
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

  // Group everything shown on the page into Buy / Hold / Avoid buckets.
  // Portfolio-specific picks come first; general signals are deduplicated.
  const recommendationTickers = new Set()
  if (recommendations) {
    ;['sell_reduce', 'hold', 'add'].forEach(key =>
      (recommendations[key] || []).forEach(s => recommendationTickers.add(s.ticker))
    )
  }
  const generalSignals = filteredSignals.filter(s => !recommendationTickers.has(s.ticker))

  const buyRecs = (hasPortfolio && recommendations?.add) || []
  const holdRecs = (hasPortfolio && recommendations?.hold) || []
  const avoidRecs = (hasPortfolio && recommendations?.sell_reduce) || []

  const buySignals = generalSignals.filter(s => s.direction === 'buy')
  const holdSignals = generalSignals.filter(s => s.direction === 'hold')
  const avoidSignals = generalSignals.filter(s => s.direction === 'avoid')

  // Drives both the "What Should You Do?" stats box and the sections below,
  // so the numbers always match the cards on screen
  const displayCounts = {
    buy: buyRecs.length + buySignals.length,
    hold: holdRecs.length + holdSignals.length,
    avoid: avoidRecs.length + avoidSignals.length
  }
  const hasAnyContent = displayCounts.buy + displayCounts.hold + displayCounts.avoid > 0

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
            <h2>💡 Hot Picks This Week</h2>
            <p>AI-picked stocks based on current market conditions</p>
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
      {stats && (
        <RecommendationStats
          stats={stats}
          generatedAt={generatedAt}
          displayCounts={displayCounts}
        />
      )}

      {/* Filters */}
      {signals.length > 0 && (
        <FilterBar onFilterChange={handleFilterChange} stats={stats} />
      )}

      {/* Signals organized by action: Buy → Hold → Avoid.
          Portfolio-specific picks appear first within each section. */}
      {displayCounts.buy > 0 && (
        <section className="signals-section buy">
          <h3 className="section-title">🟢 Buy</h3>
          <p className="section-description">
            Good buys right now — including new picks that would fit your portfolio
          </p>
          <div className="signals-grid">
            {buyRecs.map((signal, idx) => (
              <SignalCard key={`rec-${idx}`} signal={signal} type="add" />
            ))}
            {buySignals.map((signal, idx) => (
              <SignalCardEnhanced key={idx} signal={signal} type="buy" />
            ))}
          </div>
        </section>
      )}

      {displayCounts.hold > 0 && (
        <section className="signals-section hold">
          <h3 className="section-title">⏸️ Hold</h3>
          <p className="section-description">
            Keep what you own; wait and see before adding more
          </p>
          <div className="signals-grid">
            {holdRecs.map((signal, idx) => (
              <SignalCard
                key={`rec-${idx}`}
                signal={signal}
                type="hold"
                weight={signal.weight_in_portfolio}
              />
            ))}
            {holdSignals.map((signal, idx) => (
              <SignalCardEnhanced key={idx} signal={signal} type="hold" />
            ))}
          </div>
        </section>
      )}

      {hasAnyContent && (
        <section className="signals-section avoid">
          <h3 className="section-title">🔴 Avoid / Sell</h3>
          <p className="section-description">
            Skip these for now — or consider selling if you already own them
          </p>
          {displayCounts.avoid > 0 ? (
            <div className="signals-grid">
              {avoidRecs.map((signal, idx) => (
                <SignalCard
                  key={`rec-${idx}`}
                  signal={signal}
                  type="sell-reduce"
                  weight={signal.weight_in_portfolio}
                />
              ))}
              {avoidSignals.map((signal, idx) => (
                <SignalCardEnhanced key={idx} signal={signal} type="avoid" />
              ))}
            </div>
          ) : (
            <p className="section-empty-note">
              🎉 Nothing to avoid this week — all the stocks that passed our quality screen look reasonable right now.
            </p>
          )}
        </section>
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
