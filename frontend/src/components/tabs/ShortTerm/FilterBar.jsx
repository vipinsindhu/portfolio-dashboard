import { useState } from 'react'
import './FilterBar.css'

const FALLBACK_SECTORS = [
  'Broad Market Index', 'Technology', 'Healthcare', 'Financials',
  'Consumer', 'Industrials', 'Energy', 'Utilities', 'Materials',
  'Real Estate', 'Bonds', 'Commodities', 'International Equities',
]

function FilterBar({ onFilterChange, stats, sectors: sectorsProp = [] }) {
  const [direction, setDirection] = useState('all')
  const [minConfidence, setMinConfidence] = useState(6)
  const [sector, setSector] = useState('all')
  const [isOpen, setIsOpen] = useState(false)

  const sectors = sectorsProp.length > 0 ? sectorsProp : FALLBACK_SECTORS

  const apply = (newDirection, newConfidence, newSector) => {
    const d = newDirection  !== undefined ? newDirection  : direction
    const c = newConfidence !== undefined ? newConfidence : minConfidence
    const s = newSector     !== undefined ? newSector     : sector
    setDirection(d)
    setMinConfidence(c)
    setSector(s)
    onFilterChange({ direction: d, min_confidence: c, sector: s === 'all' ? null : s })
  }

  const handleReset = () => {
    setDirection('all')
    setMinConfidence(6)
    setSector('all')
    onFilterChange({ direction: 'all', min_confidence: 6, sector: null })
  }

  const hasActiveFilters = direction !== 'all' || minConfidence !== 6 || sector !== 'all'

  return (
    <div className="filter-bar">
      <div className="filter-header">
        <button
          className="filter-toggle"
          onClick={() => setIsOpen(!isOpen)}
          aria-expanded={isOpen}
        >
          <span className="filter-text">Filters</span>
          {hasActiveFilters && <span className="filter-active-dot" />}
          <span className={`toggle-arrow ${isOpen ? 'open' : ''}`}>▼</span>
        </button>

        {hasActiveFilters && (
          <button className="reset-button" onClick={handleReset}>Clear</button>
        )}

        {stats && (
          <div className="filter-stats">
            <span className="stat-pill buy">{stats.buy_count} Buy</span>
            <span className="stat-pill hold">{stats.hold_count} Hold</span>
            <span className="stat-pill avoid">{stats.avoid_count} Avoid</span>
          </div>
        )}
      </div>

      {isOpen && (
        <div className="filter-controls">
          <div className="filter-group">
            <label htmlFor="direction-select">Direction</label>
            <select
              id="direction-select"
              value={direction}
              onChange={e => apply(e.target.value, undefined, undefined)}
              className="filter-select"
            >
              <option value="all">All</option>
              <option value="buy">🟢 Buy</option>
              <option value="hold">⏸️ Hold</option>
              <option value="avoid">🔴 Avoid</option>
            </select>
          </div>

          <div className="filter-group">
            <label htmlFor="confidence-slider">Min confidence: {minConfidence}/10</label>
            <input
              id="confidence-slider"
              type="range"
              min="1"
              max="10"
              value={minConfidence}
              onChange={e => apply(undefined, parseInt(e.target.value), undefined)}
              className="filter-slider"
            />
            <div className="confidence-labels">
              <span>1</span>
              <span>10</span>
            </div>
          </div>

          <div className="filter-group">
            <label htmlFor="sector-select">Sector</label>
            <select
              id="sector-select"
              value={sector}
              onChange={e => apply(undefined, undefined, e.target.value)}
              className="filter-select"
            >
              <option value="all">All Sectors</option>
              {sectors.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>
      )}
    </div>
  )
}

export default FilterBar
