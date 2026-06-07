import { useState, useEffect } from 'react'
import './SignalArchive.css'

function SignalArchive() {
  const [archive, setArchive] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedSector, setSelectedSector] = useState('all')

  useEffect(() => {
    const fetchArchive = async () => {
      try {
        const response = await fetch('/api/signals/archive')
        if (!response.ok) throw new Error('Failed to fetch archive')
        const data = await response.json()
        setArchive(data.signals || [])
      } catch (err) {
        console.error('Error fetching archive:', err)
        setArchive([])
      } finally {
        setLoading(false)
      }
    }

    fetchArchive()
  }, [])

  const getDirectionColor = (direction) => {
    switch (direction.toLowerCase()) {
      case 'buy':
        return 'buy'
      case 'hold':
        return 'hold'
      case 'avoid':
        return 'avoid'
      default:
        return 'neutral'
    }
  }

  const getDirectionLabel = (direction) => {
    const dir = direction.toLowerCase()
    if (dir === 'buy') return '🟢 Buy'
    if (dir === 'hold') return '🟡 Hold'
    if (dir === 'avoid') return '🔴 Avoid'
    return direction
  }

  const getOutcomeLabel = (result) => {
    if (result === 'win') return '✅ Win'
    if (result === 'loss') return '❌ Loss'
    if (result === 'pending') return '⏳ Pending'
    return 'Unrated'
  }

  const sectors = ['all', ...new Set(archive.map(s => s.sector).filter(Boolean))]
  const filtered = selectedSector === 'all'
    ? archive
    : archive.filter(s => s.sector === selectedSector)

  if (loading) {
    return <div className="archive">Loading archive...</div>
  }

  return (
    <div className="archive">
      <div className="archive-header">
        <h2>Signal Archive</h2>
        <p className="archive-subtitle">Past 12 weeks of signals with outcomes</p>
      </div>

      <div className="archive-filters">
        <div className="filter-group">
          <label>Filter by Sector:</label>
          <select value={selectedSector} onChange={(e) => setSelectedSector(e.target.value)}>
            {sectors.map(sector => (
              <option key={sector} value={sector}>
                {sector === 'all' ? 'All Sectors' : sector}
              </option>
            ))}
          </select>
        </div>
        <div className="filter-info">
          Showing {filtered.length} of {archive.length} signals
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="no-archive">
          <p>No signals found for the selected filters.</p>
        </div>
      ) : (
        <div className="archive-table">
          <table>
            <thead>
              <tr>
                <th>Ticker</th>
                <th>Signal</th>
                <th>Confidence</th>
                <th>Sector</th>
                <th>Date</th>
                <th>Outcome</th>
                <th>Accuracy</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((signal) => (
                <tr key={signal.id} className={`signal-row ${getDirectionColor(signal.direction)}`}>
                  <td className="ticker-cell">
                    <strong>{signal.ticker}</strong>
                  </td>
                  <td className="direction-cell">
                    <span className={`direction-badge ${getDirectionColor(signal.direction)}`}>
                      {getDirectionLabel(signal.direction)}
                    </span>
                  </td>
                  <td className="confidence-cell">
                    <div className="confidence-inline">
                      <div className="confidence-mini">
                        <div
                          className="confidence-mini-fill"
                          style={{ width: `${(signal.confidence / 10) * 100}%` }}
                        />
                      </div>
                      <span>{signal.confidence}/10</span>
                    </div>
                  </td>
                  <td className="sector-cell">{signal.sector || '-'}</td>
                  <td className="date-cell">
                    {new Date(signal.created_at).toLocaleDateString()}
                  </td>
                  <td className="outcome-cell">
                    {signal.result ? (
                      <span className={`outcome-badge ${signal.result}`}>
                        {getOutcomeLabel(signal.result)}
                      </span>
                    ) : (
                      <span className="outcome-badge pending">⏳ Pending</span>
                    )}
                  </td>
                  <td className="accuracy-cell">
                    {signal.accuracy_pct !== null ? `${signal.accuracy_pct}%` : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="compliance-note">
        <strong>Note:</strong> Outcomes are evaluated 30 days after signal generation based on actual
        price movement. Pending signals are awaiting the 30-day window.
      </div>
    </div>
  )
}

export default SignalArchive
