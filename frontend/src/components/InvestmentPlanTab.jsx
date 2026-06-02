import { useState } from 'react'
import { computeHealth } from '../lib/macroUtils'
import { computeRecommendation } from '../lib/recommendation'
import PlanForm from './PlanForm'
import Recommendation from './Recommendation'

function InvestmentPlanTab({ signals }) {
  const [plan, setPlan] = useState(null)

  const health = computeHealth(signals)

  const handleFormSubmit = (formData) => {
    const recommendation = computeRecommendation(
      formData.amount,
      formData.timeline,
      formData.existing,
      formData.risk,
      health.score
    )
    setPlan(recommendation)
  }

  return (
    <div>
      <h2 className="section-head">Investment Plan</h2>

      <div
        style={{
          padding: '16px',
          background: 'var(--surface2)',
          borderRadius: '8px',
          marginBottom: '24px',
          borderLeft: `3px solid ${health.color}`,
        }}
      >
        <div style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '4px' }}>
          Current Market Regime
        </div>
        <div style={{ fontSize: '16px', color: health.color, fontWeight: '500' }}>
          {health.label} ({health.score}%)
        </div>
      </div>

      <div style={{ marginBottom: '32px' }}>
        <h3 style={{ fontSize: '12px', fontWeight: '500', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--text)' }}>
          Tell us about your investment
        </h3>
        <PlanForm onSubmit={handleFormSubmit} />
      </div>

      {plan && <Recommendation plan={plan} />}
    </div>
  )
}

export default InvestmentPlanTab
