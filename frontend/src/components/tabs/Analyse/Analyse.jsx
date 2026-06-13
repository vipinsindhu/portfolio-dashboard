import { useEffect, useRef } from 'react'
import PortfolioInput from './PortfolioInput'
import PitfallDetector from './PitfallDetector'
import SignalCard from '../../shared/SignalCard'
import { usePortfolio } from '../../../context/PortfolioContext'
import './Analyse.css'

function Analyse({ demoRequested, onDemoHandled }) {
  const { hasPortfolio, analysis, ltRecommendations, stRecommendations, loading, reload } = usePortfolio()

  const analyzeButtonRef = useRef(null)
  const analysisResultsRef = useRef(null)

  // Scroll to button when portfolio first loads
  useEffect(() => {
    if (hasPortfolio && analyzeButtonRef.current) {
      analyzeButtonRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' })
      analyzeButtonRef.current.classList.add('highlight-pulse')
      const t = setTimeout(() => analyzeButtonRef.current?.classList.remove('highlight-pulse'), 3000)
      return () => clearTimeout(t)
    }
  }, [hasPortfolio])

  // Scroll to results when analysis appears
  useEffect(() => {
    if (analysis && analysisResultsRef.current) {
      setTimeout(() => analysisResultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 300)
    }
  }, [analysis])

  // Merge LT and ST recommendations for the signals summary, deduplicating by ticker.
  // LT recs take precedence over ST for the same ticker.
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
        <h2>📊 Check Your Portfolio</h2>
        <p>Upload your stocks to see if you're diversified enough</p>
      </div>

      <PortfolioInput
        onPortfolioLoaded={reload}
        onAnalyze={reload}
        autoLoadSample={demoRequested}
        onAutoLoadHandled={onDemoHandled}
      />

      {hasPortfolio && (
        <div className="manual-analyze-section">
          <button
            ref={analyzeButtonRef}
            className="btn-primary btn-large"
            onClick={reload}
            disabled={loading}
          >
            {loading ? '⏳ Checking...' : '🔍 Check My Portfolio'}
          </button>
        </div>
      )}

      {loading && (
        <div className="loading-message">
          <p>Checking your portfolio...</p>
        </div>
      )}

      {analysis && (
        <div ref={analysisResultsRef}>
          <PitfallDetector analysis={analysis} />
        </div>
      )}

      {/* Signals matched to portfolio holdings */}
      {signalsSummary && (
        <div className="portfolio-signals-section">
          <h3>📡 What the Signals Say About Your Stocks</h3>
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

      {!hasPortfolio && !analysis && (
        <div className="empty-state">
          <div className="empty-state-content">
            <div className="empty-icon">📁</div>
            <h3>Upload Your Stocks</h3>
            <p>Use CSV or add them manually</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default Analyse
