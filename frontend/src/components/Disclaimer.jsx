import { useState } from 'react'
import './Disclaimer.css'

function Disclaimer() {
  const [isExpanded, setIsExpanded] = useState(false)

  return (
    <div className="disclaimer-banner">
      <div className="disclaimer-content">
        <span className="disclaimer-icon">⚠️</span>
        <div className="disclaimer-text">
          <strong>Disclaimer:</strong> This app uses AI to generate stock recommendations.
          <button
            className="disclaimer-link"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            {isExpanded ? 'Hide' : 'Read more'}
          </button>
        </div>
      </div>

      {isExpanded && (
        <div className="disclaimer-details">
          <p>
            <strong>Not Financial Advice:</strong> This application uses artificial intelligence (AI) to generate stock
            recommendations and investment signals. These recommendations are <strong>NOT professional financial advice</strong>
            and should not be relied upon as the sole basis for making investment decisions.
          </p>

          <p>
            <strong>AI Limitations:</strong> AI-generated recommendations may contain errors, incomplete information, or
            outdated data. Markets are unpredictable, and past performance does not guarantee future results.
          </p>

          <p>
            <strong>Consult Professionals:</strong> Before making any investment decisions, please:
            <ul>
              <li>Conduct your own thorough research</li>
              <li>Consult with a licensed financial advisor</li>
              <li>Consider your personal risk tolerance and financial goals</li>
              <li>Read official company filings and reports</li>
            </ul>
          </p>

          <p>
            <strong>Risk Acknowledgment:</strong> Investing in stocks involves substantial risk, including the potential
            loss of your entire investment. This app provides informational tools only and does not guarantee profits or
            prevent losses.
          </p>

          <p style={{ fontSize: '0.85em', opacity: 0.8 }}>
            By using this app, you acknowledge that you have read this disclaimer and agree that the creators are not
            responsible for any financial losses or investment outcomes.
          </p>
        </div>
      )}
    </div>
  )
}

export default Disclaimer
