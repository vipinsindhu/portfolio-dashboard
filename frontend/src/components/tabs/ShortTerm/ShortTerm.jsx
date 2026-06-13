import SignalsTab from '../../shared/SignalsTab'
import TrackRecord from './TrackRecord'

function ShortTerm() {
  return (
    <SignalsTab
      endpoint="/api/signals/short-term"
      timeframe="short_term"
      defaultMinConfidence={6}
      title="💡 Hot Picks This Week"
      subtitle="AI-picked stocks based on current market conditions"
    >
      <TrackRecord />
    </SignalsTab>
  )
}

export default ShortTerm
