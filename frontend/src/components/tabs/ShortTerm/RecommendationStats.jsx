import { useState, useEffect } from 'react'
import './RecommendationStats.css'

function RecommendationStats({ stats, generatedAt, displayCounts }) {
  const [timeAgo, setTimeAgo] = useState('')
  const [accuracy, setAccuracy] = useState(null)

  useEffect(() => {
    fetch('/api/signals/accuracy')
      .then(res => (res.ok ? res.json() : null))
      .then(setAccuracy)
      .catch(() => setAccuracy(null))
  }, [])

  useEffect(() => {
    const updateTimeAgo = () => {
      if (!generatedAt) return

      const now = new Date()
      const generated = new Date(generatedAt)
      const diffMs = now - generated
      const diffMins = Math.floor(diffMs / 60000)
      const diffHours = Math.floor(diffMs / 3600000)
      const diffDays = Math.floor(diffMs / 86400000)

      if (diffMins < 1) {
        setTimeAgo('just now')
      } else if (diffMins < 60) {
        setTimeAgo(`${diffMins}m ago`)
      } else if (diffHours < 24) {
        setTimeAgo(`${diffHours}h ago`)
      } else if (diffDays < 7) {
        setTimeAgo(`${diffDays}d ago`)
      } else {
        setTimeAgo(new Date(generatedAt).toLocaleDateString())
      }
    }

    updateTimeAgo()
    const interval = setInterval(updateTimeAgo, 30000)
    return () => clearInterval(interval)
  }, [generatedAt])

  if (!stats) {
    return null
  }

  const confidenceLevel = stats.avg_confidence >= 8 ? 'high' : stats.avg_confidence >= 6 ? 'medium' : 'low'

  // Prefer counts of what is actually rendered on the page (including
  // portfolio-specific picks) over the raw market-signal stats
  const buyCount = displayCounts ? displayCounts.buy : stats.buy_count
  const holdCount = displayCounts ? displayCounts.hold : stats.hold_count
  const avoidCount = displayCounts ? displayCounts.avoid : stats.avoid_count

  return (
    <div className="recommendation-stats">
      <div className="stats-container">
        <div className="stat-card confidence-card">
          <div className="stat-label">How Strong Are These Ideas?</div>
          <div className={`stat-value confidence-${confidenceLevel}`}>
            {stats.avg_confidence.toFixed(1)}<span className="stat-unit">/10</span>
          </div>
          <div className="stat-confidence-bars">
            {[...Array(10)].map((_, i) => (
              <div
                key={i}
                className={`bar ${i < Math.round(stats.avg_confidence) ? 'filled' : ''}`}
              />
            ))}
          </div>
          <div className="stat-hint" style={{ marginTop: '8px', fontSize: '11px' }}>
            {confidenceLevel === 'high' && '💪 Very Strong'}
            {confidenceLevel === 'medium' && '👍 Pretty Good'}
            {confidenceLevel === 'low' && '⚠️ Be Careful'}
          </div>
        </div>

        <div className="stat-card direction-card">
          <div className="stat-label">What Should You Do?</div>
          <div className="direction-breakdown">
            <div className="direction-item buy">
              <span className="icon">🟢</span>
              <span className="count">{buyCount}</span>
              <span className="label">Buy Now</span>
            </div>
            <div className="direction-item hold">
              <span className="icon">⏸️</span>
              <span className="count">{holdCount}</span>
              <span className="label">Wait & See</span>
            </div>
            <div className="direction-item avoid">
              <span className="icon">🔴</span>
              <span className="count">{avoidCount}</span>
              <span className="label">Skip This</span>
            </div>
          </div>
        </div>

        <div className="stat-card update-card">
          <div className="stat-label">How Fresh Is This?</div>
          <div className="stat-value time-ago">{timeAgo}</div>
          <div className="stat-hint">Updates daily</div>
        </div>

        {accuracy && (
          <div className="stat-card accuracy-card">
            <div className="stat-label">Track Record</div>
            {accuracy.overall?.win_rate != null ? (
              <>
                <div className="stat-value">
                  {(accuracy.recent?.win_rate ?? accuracy.overall.win_rate).toFixed(0)}
                  <span className="stat-unit">%</span>
                </div>
                <div className="stat-hint">
                  of calls correct, checked 30 days later
                  {accuracy.recent?.evaluated > 0
                    ? ` (${accuracy.recent.evaluated} recent)`
                    : ` (${accuracy.overall.evaluated} all-time)`}
                </div>
              </>
            ) : (
              <>
                <div className="stat-value collecting">📊</div>
                <div className="stat-hint">
                  Tracking {accuracy.pending || 0} calls — first results land 30 days
                  after each signal. We publish the number either way.
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default RecommendationStats
