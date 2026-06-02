import { useState } from 'react'

function PortfolioForm({ onAddHolding }) {
  const [ticker, setTicker] = useState('')
  const [shares, setShares] = useState('')
  const [costBasis, setCostBasis] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    setError('')

    const tickerUpper = ticker.trim().toUpperCase()
    const sharesNum = parseFloat(shares)
    const costBasisNum = parseFloat(costBasis)

    if (!tickerUpper || sharesNum <= 0 || costBasisNum <= 0) {
      setError('Please fill all fields with valid positive numbers')
      return
    }

    onAddHolding({
      id: `manual-${Date.now()}`,
      ticker: tickerUpper,
      shares: sharesNum,
      costBasis: costBasisNum,
    })

    setTicker('')
    setShares('')
    setCostBasis('')
  }

  return (
    <form onSubmit={handleSubmit} style={{ marginBottom: '20px' }}>
      <div style={{ marginBottom: '12px' }}>
        <label htmlFor="ticker">Ticker Symbol</label>
        <input
          id="ticker"
          type="text"
          placeholder="AAPL"
          value={ticker}
          onChange={(e) => setTicker(e.target.value)}
          maxLength="5"
        />
      </div>

      <div style={{ marginBottom: '12px' }}>
        <label htmlFor="shares">Number of Shares</label>
        <input
          id="shares"
          type="number"
          placeholder="100"
          value={shares}
          onChange={(e) => setShares(e.target.value)}
          step="0.01"
          min="0"
        />
      </div>

      <div style={{ marginBottom: '12px' }}>
        <label htmlFor="costBasis">Cost Basis per Share ($)</label>
        <input
          id="costBasis"
          type="number"
          placeholder="150.50"
          value={costBasis}
          onChange={(e) => setCostBasis(e.target.value)}
          step="0.01"
          min="0"
        />
      </div>

      {error && (
        <div
          style={{
            color: 'var(--red)',
            fontSize: '11px',
            marginBottom: '12px',
            padding: '8px',
            background: 'var(--red-dim)',
            borderRadius: '4px',
          }}
        >
          {error}
        </div>
      )}

      <button type="submit">Add to Portfolio</button>
    </form>
  )
}

export default PortfolioForm
