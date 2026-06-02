import IndicatorCard from './IndicatorCard'

function MacroTab({ signals }) {
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
    <div>
      <h2 className="section-head">9 Key Macro Indicators</h2>
      <div className="grid-3">
        {indicatorOrder.map((key) => {
          const indicator = signals[key]
          if (!indicator) return null
          return (
            <IndicatorCard
              key={key}
              name={indicator.label}
              value={indicator.value}
              signal={indicator.signal}
              context={indicator.context}
            />
          )
        })}
      </div>
    </div>
  )
}

export default MacroTab
