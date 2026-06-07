import { useState } from 'react'
import './LessonCard.css'

function LessonCard({ lesson }) {
  const [isFlipped, setIsFlipped] = useState(false)

  const severityIcon = {
    critical: '🔴',
    warning: '🟡',
    info: '🔵'
  }

  return (
    <div className="lesson-card" onClick={() => setIsFlipped(!isFlipped)}>
      <div className={`lesson-card-inner ${isFlipped ? 'flipped' : ''}`}>
        {/* Front: Pitfall Summary */}
        <div className="lesson-card-front">
          <div className="lesson-header">
            <span className="lesson-category">{lesson.category}</span>
            <span className="lesson-difficulty">{lesson.difficulty}</span>
          </div>

          <h3 className="lesson-title">{lesson.title}</h3>

          <div className="lesson-pitfall">
            <p className="pitfall-label">⚠️ Pitfall:</p>
            <p className="pitfall-text">{lesson.pitfall}</p>
          </div>

          <div className="lesson-action">
            <p className="click-hint">Click to learn more →</p>
          </div>
        </div>

        {/* Back: Solution */}
        <div className="lesson-card-back">
          <h4 className="back-title">💡 Solution</h4>

          <div className="solution-rule">
            <p className="rule-label">Rule:</p>
            <p className="rule-text">{lesson.solution.rule}</p>
          </div>

          <div className="solution-why">
            <p className="why-label">Why it works:</p>
            <p className="why-text">{lesson.solution.why_it_works}</p>
          </div>

          <div className="solution-steps">
            <p className="steps-label">Implementation:</p>
            <ul className="steps-list">
              {lesson.solution.implementation.slice(0, 2).map((step, idx) => (
                <li key={idx}>{step}</li>
              ))}
            </ul>
          </div>

          <div className="lesson-action back">
            <p className="click-hint">← Click to go back</p>
          </div>
        </div>
      </div>

      {/* Tags */}
      <div className="lesson-tags">
        {lesson.tags.slice(0, 2).map((tag) => (
          <span key={tag} className="tag">
            {tag}
          </span>
        ))}
      </div>
    </div>
  )
}

export default LessonCard
