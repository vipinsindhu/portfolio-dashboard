import { useEffect, useRef } from 'react'
import PortfolioInput from './PortfolioInput'
import PitfallDetector from './PitfallDetector'
import SignalCard from '../../shared/SignalCard'
import { usePortfolio } from '../../../context/PortfolioContext'
import './Analyse.css'

function Analyse({ demoRequested, onDemoHandled }) {
  const { hasPortfolio, analysis, ltRecommendations, stRecommendations, loading, reload } = usePortfolio()

  const analysisResultsRef = useRef(null)

  // Scroll to results when analysis appears
  useEffect(() => {
    if (analysis && analysisResultsRef.current) {
      setTimeout(() => analysisResultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 300)
    }
  }, [analysis])

  // Merge LT and ST recommendations, deduplicating by ticker (LT takes precedence)
  const signalsSummary = (() => {
    if (!ltRecommendations && !stRecommendations) return null
    const seen = new Set()
    const pick = (bucket) => {
      const items = []
      for (const s of bucket || []) {
        if (!seen.has(s.ticker)) { seen.add(s.ticker); items.push(s) }
      }
      return items
    }
    const avoid = pick([...(ltRecommendations?.sell_reduce || []), ...(stRecommendations?.sell_reduce || [])])
    const hold  = pick([...(ltRecommendations?.hold || []),        ...(stRecommendations?.hold || [])])
    const add   = pick([...(ltRecommendations?.add || []),         ...(stRecommendations?.add || [])])
    if (!avoid.length && !hold.length && !add.length) return null
    return { avoid, hold, add }
  })()

  return (
    <div className="analyse-container">
      <div className="analyse-header">
        <h2>Check Your Portfolio</h2>
        <p>Upload your stocks to see risks, concentration issues, and what the AI signals say about what you own</p>
      </div>

      <PortfolioInput
        autoLoadSample={demoRequested}
        onAutoLoadHandled={onDemoHandled}
      />

      {loading && (
        <div className="loading-message">
          <p>Checking your portfolio…</p>
        </div>
      )}

      {/* Signals matched to portfolio — shown first, more actionable than pitfalls */}
      {signalsSummary && (
        <div ref={analysisResultsRef} className="portfolio-signals-section">
          <h3>What the signals say about your stocks</h3>
          <p className="portfolio-signals-intro">
            Based on current AI signals, here's what to do with the stocks you own.
          </p>

          {signalsSummary.avoid.length > 0 && (
            <div className="portfolio-signals-group">
              <h4 className="signals-group-title signals-group-avoid">🔴 Consider Selling</h4>
              <div className="portfolio-signals-grid">
                {signalsSummary.avoid.map((s, i) => (
                  <SignalCard key={i} signal={s} type="sell-reduce" weight={s.weight_in_portfolio} />
                ))}
              </div>
            </div>
          )}

          {signalsSummary.hold.length > 0 && (
            <div className="portfolio-signals-group">
              <h4 className="signals-group-title signals-group-hold">⏸️ Hold for Now</h4>
              <div className="portfolio-signals-grid">
                {signalsSummary.hold.map((s, i) => (
                  <SignalCard key={i} signal={s} type="hold" weight={s.weight_in_portfolio} />
                ))}
              </div>
            </div>
          )}

          {signalsSummary.add.length > 0 && (
            <div className="portfolio-signals-group">
              <h4 className="signals-group-title signals-group-add">🟢 Good to Add More</h4>
              <div className="portfolio-signals-grid">
                {signalsSummary.add.map((s, i) => (
                  <SignalCard key={i} signal={s} type="add" />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Pitfall analysis — shown below signals */}
      {analysis && (
        <div ref={signalsSummary ? null : analysisResultsRef}>
          <PitfallDetector analysis={analysis} />
        </div>
      )}

      {/* Re-run button — only shown once results exist */}
      {hasPortfolio && analysis && (
        <div className="rerun-section">
          <button className="btn-secondary" onClick={reload} disabled={loading}>
            {loading ? 'Checking…' : '↺ Re-run analysis'}
          </button>
        </div>
      )}
    </div>
  )
}

export default Analyse
