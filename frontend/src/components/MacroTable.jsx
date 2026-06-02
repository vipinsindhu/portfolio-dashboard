import { getSignalText } from '../lib/macroUtils'

function MacroTable({ signals }) {
  const indicatorOrder = [
    'fed_rate',
    'treasury_yield',
    'inflation',
    'pe_ratio',
    'dollar_index',
    'vix',
    'gdp',
    'gold',
    'em_trend',
  ]

  return (
    <div className="chart-card">
      <div className="chart-card-title">Macro Signals Summary</div>
      <table>
        <thead>
          <tr>
            <th>Indicator</th>
            <th>Value</th>
            <th>Signal</th>
            <th>Context</th>
          </tr>
        </thead>
        <tbody>
          {indicatorOrder.map((key) => {
            const indicator = signals[key]
            if (!indicator) return null
            return (
              <tr key={key}>
                <td>{indicator.label}</td>
                <td>{indicator.value}</td>
                <td>{getSignalText(indicator.signal)}</td>
                <td>{indicator.context}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default MacroTable
