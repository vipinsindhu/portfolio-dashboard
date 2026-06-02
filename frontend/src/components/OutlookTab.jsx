import { computeHealth } from '../lib/macroUtils'
import HealthGauge from './HealthGauge'
import MacroTable from './MacroTable'
import RegimeCard from './RegimeCard'

function OutlookTab({ signals }) {
  const health = computeHealth(signals)

  return (
    <div>
      <h2 className="section-head">Market Outlook</h2>

      <div className="grid-2" style={{ marginBottom: '20px' }}>
        <HealthGauge
          score={health.score}
          label={health.label}
          color={health.color}
        />
        <RegimeCard />
      </div>

      <div style={{ marginTop: '20px' }}>
        <div className="chart-card">
          <div className="chart-card-title">Signal Breakdown</div>
          <div className="grid-3" style={{ marginTop: '16px' }}>
            <div style={{ textAlign: 'center', padding: '12px', backgroundColor: 'var(--surface2)', borderRadius: '8px' }}>
              <div style={{ fontSize: '20px', color: 'var(--green)', fontWeight: '500' }}>
                {health.posCount}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '4px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                Tailwinds
              </div>
            </div>
            <div style={{ textAlign: 'center', padding: '12px', backgroundColor: 'var(--surface2)', borderRadius: '8px' }}>
              <div style={{ fontSize: '20px', color: 'var(--blue)', fontWeight: '500' }}>
                {health.neutralCount}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '4px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                Neutral
              </div>
            </div>
            <div style={{ textAlign: 'center', padding: '12px', backgroundColor: 'var(--surface2)', borderRadius: '8px' }}>
              <div style={{ fontSize: '20px', color: 'var(--red)', fontWeight: '500' }}>
                {health.negCount}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--muted)', marginTop: '4px', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                Headwinds
              </div>
            </div>
          </div>
        </div>
      </div>

      <MacroTable signals={signals} />
    </div>
  )
}

export default OutlookTab
