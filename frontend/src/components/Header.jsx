import { useState } from 'react'
import FeedbackForm from './FeedbackForm'
import './Header.css'

function Header() {
  const [showFeedback, setShowFeedback] = useState(false)

  return (
    <>
      <div className="header">
        <div className="header-content">
          <h1>📊 Smart Stock Ideas</h1>
        </div>
        <div className="header-subtitle">
          <span>Get AI stock picks · Check your portfolio · Learn to invest</span>
          <button
            className="btn-feedback"
            onClick={() => setShowFeedback(true)}
            title="Send us your feedback"
          >
            💬 Feedback
          </button>
        </div>
      </div>

      {showFeedback && (
        <FeedbackForm onClose={() => setShowFeedback(false)} />
      )}
    </>
  )
}

export default Header
