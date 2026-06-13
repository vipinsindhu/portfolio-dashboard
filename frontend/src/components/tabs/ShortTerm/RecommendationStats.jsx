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
    const update = () => {
      if (!generatedAt) return
      const diffMs = Date.now() - new Date(generatedAt)
      const mins = Math.floor(diffMs / 60000)
      const hours = Math.floor(diffMs / 3600000)
      const days = Math.floor(diffMs / 86400000)
      if (mins < 1) setTimeAgo('just now')
      else if (mins < 60) setTimeAgo(`${mins}m ago`)
      else if (hours < 24) setTimeAgo(`${hours}h ago`)
      else if (days < 7) setTimeAgo(`${days}d ago`)
      else setTimeAgo(new Date(generatedAt).toLocaleDateString())
    }
    update()
    const id = setInterval(update, 60000)
    return () => clearInterval(id)
  }, [generatedAt])

  if (!stats) return null

  const buyCount   = displayCounts ? displayCounts.buy   : stats.buy_count
  const holdCount  = displayCounts ? displayCounts.hold  : stats.hold_count
  const avoidCount = displayCounts ? displayCounts.avoid : stats.avoid_count
  const conf = stats.avg_confidence
  const confLevel = conf >= 8 ? 'high' : conf >= 6 ? 'medium' : 'low'

  const winRate = accuracy?.overall?.win_rate != null
    ? (accuracy.recent?.win_rate ?? accuracy.overall.win_rate).toFixed(0)
    : null
  const evalCount = accuracy?.recent?.evaluated || accuracy?.overall?.evaluated || 0

  return (
    <div className="signal-meta-bar">
      <div className="meta-counts">
        <span className="meta-count buy">{buyCount} Buy</span>
        <span className="meta-sep">·</span>
        <span className="meta-count hold">{holdCount} Hold</span>
        <span className="meta-sep">·</span>
        <span className="meta-count avoid">{avoidCount} Avoid</span>
      </div>
      <div className="meta-right">
        <span className={`meta-confidence conf-${confLevel}`}>
          Avg {conf.toFixed(1)}/10
        </span>
        {winRate !== null && evalCount > 0 && (
          <span className="meta-accuracy">· {winRate}% accuracy ({evalCount} calls)</span>
        )}
        {timeAgo && <span className="meta-time">· {timeAgo}</span>}
      </div>
    </div>
  )
}

export default RecommendationStats
