function PortfolioSummary({ holdings, onRemoveHolding }) {
  if (holdings.length === 0) {
    return (
      <div
        style={{
          padding: '20px',
          background: 'var(--surface2)',
          borderRadius: '8px',
          textAlign: 'center',
          color: 'var(--muted)',
          marginBottom: '20px',
        }}
      >
        No holdings yet. Add one above to get started.
      </div>
    )
  }

  const totalValue = holdings.reduce((sum, h) => sum + h.shares * h.costBasis, 0)

  return (
    <div className="chart-card">
      <div className="chart-card-title">Current Portfolio</div>

      <table style={{ marginBottom: '16px' }}>
        <thead>
          <tr>
            <th>Ticker</th>
            <th>Shares</th>
            <th>Cost Basis</th>
            <th>Total</th>
            <th>%</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {holdings.map((h) => {
            const value = h.shares * h.costBasis
            const pct = ((value / totalValue) * 100).toFixed(1)
            return (
              <tr key={h.id}>
                <td style={{ textAlign: 'left' }}>{h.ticker}</td>
                <td>{h.shares.toFixed(2)}</td>
                <td>${h.costBasis.toFixed(2)}</td>
                <td>${value.toFixed(2)}</td>
                <td>{pct}%</td>
                <td style={{ textAlign: 'center' }}>
                  <button
                    onClick={() => onRemoveHolding(h.id)}
                    style={{
                      background: 'var(--red-dim)',
                      color: 'var(--red)',
                      border: '1px solid var(--red)',
                      padding: '4px 8px',
                      cursor: 'pointer',
                      borderRadius: '4px',
                      fontSize: '10px',
                    }}
                  >
                    Remove
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>

      <div
        style={{
          padding: '12px',
          background: 'var(--surface2)',
          borderRadius: '8px',
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '12px',
        }}
      >
        <div>
          <div style={{ fontSize: '10px', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>
            Total Holdings
          </div>
          <div style={{ fontSize: '18px', fontFamily: 'Fraunces, serif', fontWeight: '300' }}>
            {holdings.length}
          </div>
        </div>
        <div>
          <div style={{ fontSize: '10px', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: '4px' }}>
            Portfolio Value
          </div>
          <div style={{ fontSize: '18px', fontFamily: 'Fraunces, serif', fontWeight: '300', color: 'var(--green)' }}>
            ${totalValue.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  )
}

export default PortfolioSummary
