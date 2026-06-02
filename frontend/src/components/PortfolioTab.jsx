import { useState } from 'react'
import CSVUpload from './CSVUpload'
import PortfolioForm from './PortfolioForm'
import PortfolioSummary from './PortfolioSummary'

function PortfolioTab({ holdings, onHoldingsChange }) {
  const [showForm, setShowForm] = useState(false)

  const handleAddHolding = (holding) => {
    onHoldingsChange([...holdings, holding])
  }

  const handleRemoveHolding = (id) => {
    onHoldingsChange(holdings.filter(h => h.id !== id))
  }

  const handleClearAll = () => {
    if (window.confirm('Clear all holdings?')) {
      onHoldingsChange([])
    }
  }

  return (
    <div>
      <h2 className="section-head">Portfolio Management</h2>

      <div style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '12px', fontWeight: '500', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text)' }}>
          Load Holdings
        </h3>
        <CSVUpload onDataLoaded={onHoldingsChange} />
      </div>

      <div style={{ marginBottom: '24px' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '12px',
          }}
        >
          <h3 style={{ fontSize: '12px', fontWeight: '500', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text)', margin: 0 }}>
            Add Holding Manually
          </h3>
          <button
            onClick={() => setShowForm(!showForm)}
            style={{
              padding: '6px 12px',
              fontSize: '10px',
              background: showForm ? 'var(--accent)' : 'var(--surface2)',
              color: showForm ? 'var(--bg)' : 'var(--text)',
              border: showForm ? 'none' : '1px solid var(--border)',
              borderRadius: '4px',
              cursor: 'pointer',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
            }}
          >
            {showForm ? 'Hide Form' : 'Show Form'}
          </button>
        </div>
        {showForm && <PortfolioForm onAddHolding={handleAddHolding} />}
      </div>

      <PortfolioSummary holdings={holdings} onRemoveHolding={handleRemoveHolding} />

      {holdings.length > 0 && (
        <button
          onClick={handleClearAll}
          style={{
            width: '100%',
            padding: '12px',
            background: 'var(--red-dim)',
            color: 'var(--red)',
            border: '1px solid var(--red)',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '11px',
            fontWeight: '500',
            textTransform: 'uppercase',
            letterSpacing: '0.08em',
            marginTop: '16px',
          }}
        >
          Clear All Holdings
        </button>
      )}
    </div>
  )
}

export default PortfolioTab
