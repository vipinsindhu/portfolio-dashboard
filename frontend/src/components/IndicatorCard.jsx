import { getSignalBadgeClass, getSignalText } from '../lib/macroUtils'

function IndicatorCard({ name, value, signal, context }) {
  const pct = Math.min(Math.max((signal + 1) / 2 * 100, 0), 100)
  const fillColor =
    signal > 0 ? 'var(--green)' : signal < 0 ? 'var(--red)' : 'var(--blue)'

  return (
    <div className="indicator">
      <div className="ind-header">
        <div>
          <div className="ind-name">{name}</div>
          <div className="ind-value">{value}</div>
        </div>
        <span className={`signal ${getSignalBadgeClass(signal)}`}>
          {getSignalText(signal)}
        </span>
      </div>
      <div className="ind-desc">{context}</div>
      <div className="gauge-track">
        <div
          className="gauge-fill"
          style={{
            width: `${pct}%`,
            backgroundColor: fillColor,
          }}
        />
      </div>
    </div>
  )
}

export default IndicatorCard
