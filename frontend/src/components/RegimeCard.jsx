import { REGIMES } from '../lib/macroUtils'

function RegimeCard() {
  return (
    <div className="chart-card">
      <div className="chart-card-title">Market Regime Guide</div>
      <div style={{ marginTop: '16px' }}>
        {REGIMES.map((regime, idx) => (
          <div
            key={idx}
            style={{
              padding: '12px',
              marginBottom: '8px',
              backgroundColor: 'var(--surface2)',
              borderRadius: '6px',
              borderLeft: `3px solid ${regime.color}`,
            }}
          >
            <div style={{ fontSize: '11px', fontWeight: '500', color: regime.color, marginBottom: '4px' }}>
              {regime.label} ({regime.score})
            </div>
            <div style={{ fontSize: '11px', color: 'var(--muted)' }}>
              {regime.action}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default RegimeCard
