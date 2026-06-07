import { useState, useEffect } from 'react'
import LessonCard from './LessonCard'
import './Learn.css'

function Learn() {
  const [lessons, setLessons] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch lessons
  useEffect(() => {
    fetchLessons()
  }, [])

  const fetchLessons = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/learn/lessons')
      if (!response.ok) throw new Error('Failed to fetch lessons')
      const data = await response.json()
      setLessons(data.lessons)
      setError(null)
    } catch (err) {
      console.error('Error fetching lessons:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="learn-container loading">Loading lessons...</div>
  }

  return (
    <div className="learn-container">
      <div className="learn-header">
        <h2>📚 Learn Investment Basics</h2>
        <p>Click any card to flip and learn how to protect your money</p>
      </div>

      {error && <div className="error-message">Error: {error}</div>}

      {/* Lessons Grid */}
      <div className="lessons-grid">
        {lessons.map((lesson) => (
          <LessonCard key={lesson.id} lesson={lesson} />
        ))}
      </div>
    </div>
  )
}

export default Learn
