import { useState } from 'react'
import './TrackRecord.css'

// Pre-registered track record: every signal is logged the day we publish it
// and scored after its window (30d short-term, 90d vs SPY long-term).
function TrackRecord() {
  const [expanded, setExpanded] = useState(false)
  const [entries, setEntries] = useState(null)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const loadHistory = async () => {
    if (entries !== null || loading) return
    setLoading(true)
    try {
      const response = await fetch('/api/signals/history?limit=150')
      if (!response.ok) throw new Error('Failed to load track record')
      const data = await response.json()
      setEntries(data.entries || [])
      setStats(data.stats || null)
    } catch (err) {
      console.error('Error loading track record:', err)
      setError('Could not load the track record right now')
    } finally {
      setLoading(false)
    }
  }

  const toggle = () => {
    const next = !expanded
    setExpanded(next)
    if (next) loadHistory()
  }

  const weekLabel = (isoDate) => {
    const d = new Date(isoDate)
    if (isNaN(d)) return 'Earlier'
    const monday = new Date(d)
    monday.setDate(d.getDate() - ((d.getDay() + 6) % 7))
    return `Week of ${monday.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}`
  }

  const dueDate = (entry) => {
    const d = new Date(entry.created_at)
    if (isNaN(d)) return null
    d.setDate(d.getDate() + (entry.timeframe === 'long_term' ? 90 : 30))
    return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
  }

  const outcomeBadge = (entry) => {
    if (entry.result === 'win') {
      return (
        <span className="outcome win">
          ✅ Win {entry.return_pct > 0 ? '+' : ''}{entry.return_pct}%
          {entry.benchmark_return_pct != null && (
            <em> vs SPY {entry.benchmark_return_pct > 0 ? '+' : ''}{entry.benchmark_return_pct}%</em>
          )}
        </span>
      )
    }
    if (entry.result === 'loss') {
      return (
        <span className="outcome loss">
          ❌ Loss {entry.return_pct > 0 ? '+' : ''}{entry.return_pct}%
          {entry.benchmark_return_pct != null && (
            <em> vs SPY {entry.benchmark_return_pct > 0 ? '+' : ''}{entry.benchmark_return_pct}%</em>
          )}
        </span>
      )
    }
    if (entry.result === null) {
      const due = dueDate(entry)
      return <span className="outcome pending">⏳ Results {due ? `~${due}` : 'pending'}</span>
    }
    return <span className="outcome na">—</span>
  }

  // Group entries by week, preserving newest-first order
  const groups = []
  if (entries) {
    let current = null
    for (const entry of entries) {
      const label = weekLabel(entry.created_at)
      if (!current || current.label !== label) {
        current = { label, items: [] }
        groups.push(current)
      }
      current.items.push(entry)
    }
  }

  const evaluated = stats?.overall?.evaluated || 0
  const firstPendingDue = entries?.length
    ? entries.filter(e => e.result === null).map(dueDate).filter(Boolean).pop()
    : null

  return (
    <section className="track-record">
      <button className="track-record-toggle" onClick={toggle} aria-expanded={expanded}>
        <span className="toggle-title">📜 Track Record</span>
        <span className="toggle-subtitle">
          Every call we publish is logged and scored — see how past picks turned out
        </span>
        <span className="toggle-chevron">{expanded ? '▲' : '▼'}</span>
      </button>

      {expanded && (
        <div className="track-record-body">
          {loading && <p className="track-record-note">⏳ Loading…</p>}
          {error && <p className="track-record-note">{error}</p>}

          {entries && entries.length === 0 && (
            <p className="track-record-note">
              No history yet — signals start being logged the day they're published.
            </p>
          )}

          {entries && entries.length > 0 && (
            <>
              <div className="track-record-summary">
                {evaluated > 0 ? (
                  <>
                    <strong>{stats.overall.win_rate}%</strong> win rate over {evaluated} scored call{evaluated === 1 ? '' : 's'}
                    {' '}({stats.pending} still pending)
                  </>
                ) : (
                  <>
                    {entries.length} calls logged, none scored yet —
                    first results expected {firstPendingDue ? `around ${firstPendingDue}` : 'soon'}.
                    We publish before we know the outcomes.
                  </>
                )}
              </div>

              {groups.map(group => (
                <div key={group.label} className="track-record-week">
                  <h4 className="week-label">{group.label}</h4>
                  <ul className="track-record-list">
                    {group.items.map(entry => (
                      <li key={entry.id} className="track-record-row">
                        <span className={`direction-chip ${entry.direction}`}>
                          {entry.direction === 'buy' ? '🟢' : entry.direction === 'avoid' ? '🔴' : '⏸️'} {entry.direction}
                        </span>
                        <span className="row-ticker">{entry.ticker}</span>
                        <span className="row-timeframe">
                          {entry.timeframe === 'short_term' ? '1–3 mo' : '5+ yr'}
                        </span>
                        <span className="row-confidence">{entry.confidence}/10</span>
                        {outcomeBadge(entry)}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </>
          )}
        </div>
      )}
    </section>
  )
}

export default TrackRecord
