import SignalsTab from '../../shared/SignalsTab'
import './LongTerm.css'

function LongTerm() {
  return (
    <SignalsTab
      endpoint="/api/signals/long-term"
      timeframe="long_term"
      defaultMinConfidence={5}
      title="🎯 Build Wealth Long-term"
      subtitle="Quality companies to hold for years"
    >
      <div className="education-section">
        <div className="education-card">
          <h3>💡 Why Long-term Investing?</h3>
          <p>
            Patient investors make more money. Holding quality stocks for years beats trying to time the market.
            The best investors focus on good companies and keep them, ignoring short-term ups and downs.
          </p>
          <p>
            Use the filters to find stocks you're comfortable holding for years. The higher the confidence score, the better the stock looks for the long run.
          </p>
        </div>
      </div>
    </SignalsTab>
  )
}

export default LongTerm
