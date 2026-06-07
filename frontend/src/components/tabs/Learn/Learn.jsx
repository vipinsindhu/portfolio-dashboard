import { useState, useEffect } from 'react'
import LessonCard from './LessonCard'
import './Learn.css'

function Learn() {
  const [lessons, setLessons] = useState([])
  const [filteredLessons, setFilteredLessons] = useState([])
  const [categories, setCategories] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [selectedDifficulty, setSelectedDifficulty] = useState('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Fetch categories
  useEffect(() => {
    fetchCategories()
  }, [])

  // Fetch lessons
  useEffect(() => {
    fetchLessons()
  }, [])

  // Filter lessons when selection changes
  useEffect(() => {
    filterLessons()
  }, [lessons, selectedCategory, selectedDifficulty])

  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/learn/categories')
      if (!response.ok) throw new Error('Failed to fetch categories')
      const data = await response.json()
      setCategories(data.categories)
    } catch (err) {
      console.error('Error fetching categories:', err)
      setError(err.message)
    }
  }

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

  const filterLessons = () => {
    let filtered = lessons

    if (selectedCategory !== 'all') {
      filtered = filtered.filter((l) => l.category === selectedCategory)
    }

    if (selectedDifficulty !== 'all') {
      filtered = filtered.filter((l) => l.difficulty === selectedDifficulty)
    }

    setFilteredLessons(filtered)
  }

  if (loading) {
    return <div className="learn-container loading">Loading lessons...</div>
  }

  return (
    <div className="learn-container">
      <div className="learn-header">
        <h2>📚 Learn About Investing Pitfalls</h2>
        <p>Click cards to flip and learn how to avoid common mistakes</p>
      </div>

      {error && <div className="error-message">Error: {error}</div>}

      {/* Filters */}
      <div className="learn-filters">
        <div className="filter-group">
          <label htmlFor="category-filter">Category:</label>
          <select
            id="category-filter"
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
          >
            <option value="all">All Categories</option>
            {categories.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="difficulty-filter">Difficulty:</label>
          <select
            id="difficulty-filter"
            value={selectedDifficulty}
            onChange={(e) => setSelectedDifficulty(e.target.value)}
          >
            <option value="all">All Levels</option>
            <option value="beginner">Beginner</option>
            <option value="intermediate">Intermediate</option>
            <option value="advanced">Advanced</option>
          </select>
        </div>

        <div className="filter-reset">
          <button
            className="btn-secondary"
            onClick={() => {
              setSelectedCategory('all')
              setSelectedDifficulty('all')
            }}
          >
            Reset Filters
          </button>
        </div>
      </div>

      {/* Lessons Grid */}
      <div className="lessons-grid">
        {filteredLessons.length > 0 ? (
          filteredLessons.map((lesson) => (
            <LessonCard key={lesson.id} lesson={lesson} />
          ))
        ) : (
          <div className="no-lessons">
            <p>No lessons match your filters</p>
          </div>
        )}
      </div>

      <div className="lessons-summary">
        <p>
          Showing {filteredLessons.length} of {lessons.length} lessons
        </p>
      </div>
    </div>
  )
}

export default Learn
