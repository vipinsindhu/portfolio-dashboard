function Recommendation({ plan }) {
  if (!plan) return null

  return (
    <div className="recommendation-box">
      <div
        style={{
          fontSize: '14px',
          fontWeight: '500',
          marginBottom: '16px',
          color: plan.regimeColor,
        }}
      >
        {plan.regimeLabel} Market Regime
      </div>

      <div>
        <div style={{ fontSize: '11px', fontWeight: '500', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Recommended Allocation
        </div>
        <div className="allocation-box">
          <div className="allocation-item">
            <div className="allocation-pct" style={{ color: '#60a5fa' }}>
              {plan.equityAlloc}%
            </div>
            <div className="allocation-label">Stocks</div>
          </div>
          <div className="allocation-item">
            <div className="allocation-pct" style={{ color: '#a78bfa' }}>
              {plan.bondAlloc}%
            </div>
            <div className="allocation-label">Bonds</div>
          </div>
          <div className="allocation-item">
            <div className="allocation-pct" style={{ color: '#fbbf24' }}>
              {plan.cashAlloc}%
            </div>
            <div className="allocation-label">Cash / Alt</div>
          </div>
        </div>
      </div>

      <div style={{ marginTop: '20px' }}>
        <div style={{ fontSize: '11px', fontWeight: '500', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
          Recommended ETFs
        </div>
        <div className="funds-list">
          {Object.entries(plan.funds).map(([category, etfs]) => (
            <div key={category} className="funds-category">
              <div className="funds-category-title">
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </div>
              <ul>
                {etfs.map((etf) => (
                  <li key={etf}>{etf}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>

      <div className="disclaimer">
        <strong>Disclaimer:</strong> This is not financial advice. Consult a financial advisor
        before making investment decisions. All investing carries risk, including potential
        loss of principal.
      </div>
    </div>
  )
}

export default Recommendation
