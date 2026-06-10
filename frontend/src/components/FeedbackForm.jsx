import { useState } from 'react'
import './FeedbackForm.css'

function FeedbackForm({ onClose }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    tab: '',
    usefulness: '',
    experience: '',
    features: [],
    feedback: '',
    willUse: ''
  })

  const [loading, setLoading] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState(null)

  const handleInputChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleCheckboxChange = (feature) => {
    setFormData(prev => ({
      ...prev,
      features: prev.features.includes(feature)
        ? prev.features.filter(f => f !== feature)
        : [...prev.features, feature]
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    // Validate required fields
    if (!formData.tab || !formData.usefulness || !formData.willUse) {
      setError('Please fill in all required fields')
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Prepare form data for Formspree
      const formContent = `
Name: ${formData.name || '(Not provided)'}
Email: ${formData.email || '(Not provided)'}
Tab Used: ${formData.tab}
Usefulness Rating: ${formData.usefulness}/5
Experience Level: ${formData.experience || '(Not provided)'}
Improvements Needed: ${formData.features.length > 0 ? formData.features.join(', ') : '(None selected)'}
Additional Feedback: ${formData.feedback || '(None)'}
Will Use Regularly: ${formData.willUse}
      `.trim()

      // Send to Formspree
      const response = await fetch('https://formspree.io/f/xzdqveyo', {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: formContent,
          email: formData.email || 'noreply@example.com'
        })
      })

      if (response.ok) {
        setSubmitted(true)
        setTimeout(() => onClose(), 2000)
      } else {
        setError('Failed to submit feedback. Please try again.')
      }
    } catch (err) {
      setError('Error submitting feedback. Please try again.')
      console.error('Feedback submission error:', err)
    } finally {
      setLoading(false)
    }
  }

  if (submitted) {
    return (
      <div className="feedback-modal-overlay" onClick={onClose}>
        <div className="feedback-modal" onClick={e => e.stopPropagation()}>
          <div className="feedback-success">
            <div className="success-icon">✓</div>
            <h3>Thank You!</h3>
            <p>Your feedback helps us improve. We appreciate your input!</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="feedback-modal-overlay" onClick={onClose}>
      <div className="feedback-modal" onClick={e => e.stopPropagation()}>
        <div className="feedback-header">
          <h2>📝 Help Us Improve</h2>
          <p>Your feedback helps us build better stock recommendations</p>
          <button className="feedback-close" onClick={onClose}>✕</button>
        </div>

        <form onSubmit={handleSubmit} className="feedback-form">
          {/* Name */}
          <div className="form-group">
            <label>Name (optional)</label>
            <input
              type="text"
              name="name"
              placeholder="Your name"
              value={formData.name}
              onChange={handleInputChange}
            />
          </div>

          {/* Email */}
          <div className="form-group">
            <label>Email (optional - for follow-up)</label>
            <input
              type="email"
              name="email"
              placeholder="your@email.com"
              value={formData.email}
              onChange={handleInputChange}
            />
          </div>

          {/* Tab Used */}
          <div className="form-group">
            <label>
              Which tab did you use? <span className="required">*</span>
            </label>
            <div className="radio-group">
              {[
                { value: 'this-week', label: '💡 This Week (Short-term)' },
                { value: 'build-wealth', label: '🎯 Build Wealth (Long-term)' },
                { value: 'my-stocks', label: '📊 My Stocks (Portfolio)' },
                { value: 'learn', label: '📚 Learn' },
                { value: 'multiple', label: 'Multiple tabs' }
              ].map(option => (
                <label key={option.value} className="radio-label">
                  <input
                    type="radio"
                    name="tab"
                    value={option.value}
                    checked={formData.tab === option.value}
                    onChange={handleInputChange}
                  />
                  {option.label}
                </label>
              ))}
            </div>
          </div>

          {/* Usefulness Rating */}
          <div className="form-group">
            <label>
              How useful were the stock picks? <span className="required">*</span>
            </label>
            <div className="rating-group">
              {[1, 2, 3, 4, 5].map(rating => (
                <label key={rating} className="rating-label">
                  <input
                    type="radio"
                    name="usefulness"
                    value={rating}
                    checked={formData.usefulness === String(rating)}
                    onChange={handleInputChange}
                  />
                  <span className="rating-stars">{'⭐'.repeat(rating)}</span>
                  <span className="rating-text">
                    {rating === 1 && 'Not useful'}
                    {rating === 2 && 'Somewhat useful'}
                    {rating === 3 && 'Useful'}
                    {rating === 4 && 'Very useful'}
                    {rating === 5 && 'Extremely useful'}
                  </span>
                </label>
              ))}
            </div>
          </div>

          {/* Experience Level */}
          <div className="form-group">
            <label>Investment experience (optional)</label>
            <select
              name="experience"
              value={formData.experience}
              onChange={handleInputChange}
            >
              <option value="">Select...</option>
              <option value="beginner">Beginner</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
              <option value="professional">Professional</option>
            </select>
          </div>

          {/* Feature Requests */}
          <div className="form-group">
            <label>What would make this more helpful? (optional)</label>
            <div className="checkbox-group">
              {[
                { value: 'better-explanations', label: 'Better explanation of recommendations' },
                { value: 'more-filters', label: 'More filtering options' },
                { value: 'accuracy-data', label: 'Historical accuracy data' },
                { value: 'risk-assessment', label: 'Risk assessment details' },
                { value: 'mobile-app', label: 'Mobile app' },
                { value: 'broker-integration', label: 'Integration with brokers' }
              ].map(feature => (
                <label key={feature.value} className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={formData.features.includes(feature.value)}
                    onChange={() => handleCheckboxChange(feature.value)}
                  />
                  {feature.label}
                </label>
              ))}
            </div>
          </div>

          {/* Additional Feedback */}
          <div className="form-group">
            <label>Additional feedback (optional)</label>
            <textarea
              name="feedback"
              placeholder="What else should we know? (max 500 characters)"
              value={formData.feedback}
              onChange={handleInputChange}
              maxLength={500}
              rows={4}
            />
            <div className="char-count">{formData.feedback.length}/500</div>
          </div>

          {/* Usage Intent */}
          <div className="form-group">
            <label>
              Would you use this regularly? <span className="required">*</span>
            </label>
            <div className="radio-group">
              {[
                { value: 'yes', label: 'Yes, definitely' },
                { value: 'maybe', label: 'Maybe' },
                { value: 'no', label: 'No' }
              ].map(option => (
                <label key={option.value} className="radio-label">
                  <input
                    type="radio"
                    name="willUse"
                    value={option.value}
                    checked={formData.willUse === option.value}
                    onChange={handleInputChange}
                  />
                  {option.label}
                </label>
              ))}
            </div>
          </div>

          {/* Error Message */}
          {error && <div className="error-message">{error}</div>}

          {/* Submit Buttons */}
          <div className="form-actions">
            <button type="submit" className="btn-submit" disabled={loading}>
              {loading ? '⏳ Sending...' : '✓ Send Feedback'}
            </button>
            <button type="button" className="btn-cancel" onClick={onClose}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default FeedbackForm
