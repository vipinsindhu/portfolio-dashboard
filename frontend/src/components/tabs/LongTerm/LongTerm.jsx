import SignalsTab from '../../shared/SignalsTab'

function LongTerm() {
  return (
    <SignalsTab
      endpoint="/api/signals/long-term"
      timeframe="long_term"
      defaultMinConfidence={5}
      title="Build Wealth Long-term"
      subtitle="Quality companies to hold for years — patience beats timing the market"
    />
  )
}

export default LongTerm
