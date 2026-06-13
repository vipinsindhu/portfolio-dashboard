import { useState, useEffect } from 'react'
import './FilterBar.css'

function FilterBar({ onFilterChange, stats }) {
  const [direction, setDirection] = useState('all')
  const [minConfidence, setMinConfidence] = useState(6)
  const [sector, setSector] = useState('all')
  const [sectors, setSectors] = useState([])
  const [isOpen, setIsOpen] = useState(false)

  useEffect(() => {
    fetchAvailableSectors()
  }, [stats])

  const fetchAvailableSectors = async () => {
    try {
      // Fetch all signals to extract unique sectors
      const response = await fetch('/api/signals/short-term?limit=100')
      if (!response.ok) throw new Error('Failed to fetch signals')
      const data = await response.json()

      // Extract unique sectors from signals
      const uniqueSectors = [...new Set(
        (data.signals || []).map(s => s.sector).filter(Boolean)
      )].sort()

      setSectors(uniqueSectors.length > 0 ? uniqueSectors : [
        'Broad Market Index',
        'Technology',
        'Healthcare',
        'Financials',
        'Consumer',
        'Industrials',
        'Energy',
        'Utilities',
        'Materials',
        'Real Estate',
        'Bonds',
        'Commodities',
        'Cryptocurrencies',
        'International Equities',
      ])
    } catch (err) {
      // Fallback to predefined sectors if fetch fails
      setSectors([
        'Broad Market Index',
        'Technology',
        'Healthcare',
        'Financials',
        'Consumer',
        'Industrials',
        'Energy',
        'Utilities',
        'Materials',
        'Real Estate',
        'Bonds',
        'Commodities',
        'Cryptocurrencies',
        'International Equities',
      ])
    }
  }

  const handleFilterChange = (newDirection, newConfidence, newSector) => {
    const updatedDirection = newDirection !== undefined ? newDirection : direction
    const updatedConfidence = newConfidence !== undefined ? newConfidence : minConfidence
    const updatedSector = newSector !== undefined ? newSector : sector

    setDirection(updatedDirection)
    setMinConfidence(updatedConfidence)
    setSector(updatedSector)

    onFilterChange({
      direction: updatedDirection,
      min_confidence: updatedConfidence,
      sector: updatedSector === 'all' ? null : updatedSector
    })
  }

  const handleReset = () => {
    setDirection('all')
    setMinConfidence(6)
    setSector('all')
    onFilterChange({
      direction: 'all',
      min_confidence: 6,
      sector: null
    })
  }

  return (
    <div className="filter-bar">
      <div className="filter-header">
        <button
          className="filter-toggle"
          onClick={() => setIsOpen(!isOpen)}
          aria-expanded={isOpen}
        >
          <span className="filter-icon">⚙️</span>
          <span className="filter-text">Filters</span>
          <span className={`toggle-arrow ${isOpen ? 'open' : ''}`}>▼</span>
        </button>

        {(direction !== 'all' || minConfidence !== 6 || sector !== 'all') && (
          <button className="reset-button" onClick={handleReset}>
            Clear All
          </button>
        )}
      </div>

      {isOpen && (
        <div className="filter-controls">
          {/* Direction Filter */}
          <div className="filter-group">
            <label htmlFor="direction-select">What Do You Want To Do?</label>
            <select
              id="direction-select"
              value={direction}
              onChange={(e) => handleFilterChange(e.target.value, undefined, undefined)}
              className="filter-select"
            >
              <option value="all">Show Everything</option>
              <option value="buy">🟢 Just Show Buys</option>
              <option value="hold">⏸️ Just Show Wait & See</option>
              <option value="avoid">🔴 Just Show Skip This</option>
            </select>
          </div>

          {/* Confidence Filter */}
          <div className="filter-group">
            <label htmlFor="confidence-slider">
              Only Show Strong Ideas ({minConfidence}+/10)
            </label>
            <input
              id="confidence-slider"
              type="range"
              min="1"
              max="10"
              value={minConfidence}
              onChange={(e) => handleFilterChange(undefined, parseInt(e.target.value), undefined)}
              className="filter-slider"
            />
            <div className="confidence-labels">
              <span>Low (1)</span>
              <span>High (10)</span>
            </div>
          </div>

          {/* Sector Filter */}
          <div className="filter-group">
            <label htmlFor="sector-select">Sector</label>
            <select
              id="sector-select"
              value={sector}
              onChange={(e) => handleFilterChange(undefined, undefined, e.target.value)}
              className="filter-select"
            >
              <option value="all">All Sectors</option>
              {sectors.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          {/* Active Filters Display */}
          {(direction !== 'all' || minConfidence !== 6 || sector !== 'all') && (
            <div className="active-filters">
              <div className="filters-title">Active Filters:</div>
              <div className="filter-tags">
                {direction !== 'all' && (
                  <span className="filter-tag">
                    {direction === 'buy' && '🟢'}
                    {direction === 'hold' && '⏸️'}
                    {direction === 'avoid' && '🔴'}
                    {' '}{direction.charAt(0).toUpperCase() + direction.slice(1)}
                  </span>
                )}
                {minConfidence !== 6 && (
                  <span className="filter-tag">
                    Confidence {minConfidence}+
                  </span>
                )}
                {sector !== 'all' && (
                  <span className="filter-tag">
                    {sector}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Stats Summary */}
      {stats && (
        <div className="filter-stats">
          <span className="stat-pill buy">
            {stats.buy_count} {stats.buy_count === 1 ? 'Buy' : 'Buys'}
          </span>
          <span className="stat-pill hold">
            {stats.hold_count} {stats.hold_count === 1 ? 'Hold' : 'Holds'}
          </span>
          <span className="stat-pill avoid">
            {stats.avoid_count} {stats.avoid_count === 1 ? 'Avoid' : 'Avoids'}
          </span>
        </div>
      )}
    </div>
  )
}

export default FilterBar
