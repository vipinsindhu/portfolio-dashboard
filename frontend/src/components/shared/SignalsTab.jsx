import { useState, useEffect } from 'react'
import SignalCard from './SignalCard'
import SignalCardEnhanced from '../tabs/ShortTerm/SignalCardEnhanced'
import FilterBar from '../tabs/ShortTerm/FilterBar'
import RecommendationStats from '../tabs/ShortTerm/RecommendationStats'
import { usePortfolio } from '../../context/PortfolioContext'
import './SignalsTab.css'

function SignalsTab({ endpoint, timeframe, defaultMinConfidence, title, subtitle, children }) {
  const [signals, setSignals] = useState([])
  const [filteredSignals, setFilteredSignals] = useState([])
  const [stats, setStats] = useState(null)
  const [generatedAt, setGeneratedAt] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [signalRecommendations, setSignalRecommendations] = useState(null)
  const [filters, setFilters] = useState({
    direction: 'all',
    min_confidence: defaultMinConfidence,
    sector: null,
  })

  const { hasPortfolio, ltRecommendations, stRecommendations } = usePortfolio()
  const contextRecommendations = timeframe === 'short_term' ? stRecommendations : ltRecommendations

  // Prefer inline recommendations from the signal response (always fresh with signals);
  // fall back to context (fetched once on portfolio load)
  const recommendations = signalRecommendations || contextRecommendations

  useEffect(() => {
    fetchData()
    const interval = setInterval(() => fetchData(), 3600000)
    return () => clearInterval(interval)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (filters.direction !== 'all') params.append('direction', filters.direction)
      if (filters.min_confidence !== defaultMinConfidence) params.append('min_confidence', filters.min_confidence)
      if (filters.sector) params.append('sector', filters.sector)

      const res = await fetch(`${endpoint}?${params.toString()}`)
      if (!res.ok) throw new Error('Failed to fetch signals')
      const data = await res.json()

      setSignals(data.signals || [])
      setFilteredSignals(data.signals || [])
      setStats(data.stats)
      setGeneratedAt(data.generated_at)

      if (data.recommendations) {
        setSignalRecommendations(data.recommendations)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters)
    applyFilters(signals, newFilters)
  }

  const applyFilters = (all, f) => {
    let out = all
    if (f.direction && f.direction !== 'all') out = out.filter(s => s.direction === f.direction)
    if (f.min_confidence) out = out.filter(s => s.confidence >= f.min_confidence)
    if (f.sector) out = out.filter(s => s.sector === f.sector)
    setFilteredSignals(out)
  }

  // Portfolio-specific picks come first; deduplicate from general list
  const recommendationTickers = new Set()
  if (recommendations) {
    ;['sell_reduce', 'hold', 'add'].forEach(key =>
      (recommendations[key] || []).forEach(s => recommendationTickers.add(s.ticker))
    )
  }
  const generalSignals = filteredSignals.filter(s => !recommendationTickers.has(s.ticker))

  const showPortfolio = hasPortfolio && !!recommendations
  const buyRecs    = showPortfolio ? (recommendations.add        || []) : []
  const holdRecs   = showPortfolio ? (recommendations.hold       || []) : []
  const avoidRecs  = showPortfolio ? (recommendations.sell_reduce || []) : []

  const buySignals   = generalSignals.filter(s => s.direction === 'buy')
  const holdSignals  = generalSignals.filter(s => s.direction === 'hold')
  const avoidSignals = generalSignals.filter(s => s.direction === 'avoid')

  const displayCounts = {
    buy:   buyRecs.length   + buySignals.length,
    hold:  holdRecs.length  + holdSignals.length,
    avoid: avoidRecs.length + avoidSignals.length,
  }
  const hasAnyContent = displayCounts.buy + displayCounts.hold + displayCounts.avoid > 0

  if (loading && signals.length === 0) {
    return (
      <div className="signals-tab-container signals-tab-loading">
        <div className="loading-spinner">⏳ Loading signals...</div>
      </div>
    )
  }

  return (
    <div className="signals-tab-container">
      <div className="signals-tab-header">
        <div className="header-top">
          <div>
            <h2>{title}</h2>
            <p>{subtitle}</p>
          </div>
          <button
            className="btn-refresh"
            onClick={() => { setLoading(true); fetchData() }}
            disabled={loading}
            title="Refresh signals manually"
          >
            {loading ? '⏳ Refreshing...' : '🔄 Refresh'}
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {stats && (
        <RecommendationStats stats={stats} generatedAt={generatedAt} displayCounts={displayCounts} />
      )}

      {signals.length > 0 && (
        <FilterBar onFilterChange={handleFilterChange} stats={stats} />
      )}

      {displayCounts.buy > 0 && (
        <section className="signals-section buy">
          <h3 className="section-title">🟢 Buy</h3>
          <div className="signals-grid">
            {buyRecs.map((signal, idx) => (
              <SignalCard key={`rec-buy-${idx}`} signal={signal} type="add" />
            ))}
            {buySignals.map((signal, idx) => (
              <SignalCardEnhanced key={`gen-buy-${idx}`} signal={signal} type="buy" />
            ))}
          </div>
        </section>
      )}

      {displayCounts.hold > 0 && (
        <section className="signals-section hold">
          <h3 className="section-title">⏸️ Hold</h3>
          <div className="signals-grid">
            {holdRecs.map((signal, idx) => (
              <SignalCard key={`rec-hold-${idx}`} signal={signal} type="hold" weight={signal.weight_in_portfolio} />
            ))}
            {holdSignals.map((signal, idx) => (
              <SignalCardEnhanced key={`gen-hold-${idx}`} signal={signal} type="hold" />
            ))}
          </div>
        </section>
      )}

      {hasAnyContent && (
        <section className="signals-section avoid">
          <h3 className="section-title">🔴 Avoid / Sell</h3>
          {displayCounts.avoid > 0 ? (
            <div className="signals-grid">
              {avoidRecs.map((signal, idx) => (
                <SignalCard key={`rec-avoid-${idx}`} signal={signal} type="sell-reduce" weight={signal.weight_in_portfolio} />
              ))}
              {avoidSignals.map((signal, idx) => (
                <SignalCardEnhanced key={`gen-avoid-${idx}`} signal={signal} type="avoid" />
              ))}
            </div>
          ) : (
            <p className="section-empty-note">
              🎉 Nothing to avoid right now — all the stocks that passed our quality screen look reasonable.
            </p>
          )}
        </section>
      )}

      {filteredSignals.length === 0 && (
        <div className="empty-state">
          <p>😴 No signals match your filters</p>
          <p className="empty-hint">Try changing your filters or check back later</p>
        </div>
      )}

      {/* Extra content slot: TrackRecord for ShortTerm, education card for LongTerm */}
      {children}

      {!showPortfolio && signals.length > 0 && (
        <div className="cta-section">
          <div className="cta-content">
            <h4>💼 Show Us Your Stocks?</h4>
            <p>Upload what you own and we'll personalise these picks for your portfolio</p>
            <a href="#" className="btn-primary">Go to My Stocks tab</a>
          </div>
        </div>
      )}
    </div>
  )
}

export default SignalsTab
