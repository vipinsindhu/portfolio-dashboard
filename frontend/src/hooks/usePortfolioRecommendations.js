import { useState, useEffect, useCallback } from 'react'

const CACHE_DURATION = 60000 // 1 minute TTL

let recommendationCache = {
  short_term: null,
  long_term: null,
  timestamp: 0
}

export function usePortfolioRecommendations(timeframe) {
  const [recommendations, setRecommendations] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const fetchRecommendations = useCallback(async () => {
    // Check cache first
    const now = Date.now()
    if (
      recommendationCache[timeframe] &&
      now - recommendationCache.timestamp < CACHE_DURATION
    ) {
      setRecommendations(recommendationCache[timeframe])
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await fetch(
        `/api/portfolio/recommendations?timeframe=${timeframe}`
      )
      if (response.ok) {
        const data = await response.json()
        // Update cache
        recommendationCache[timeframe] = data
        recommendationCache.timestamp = Date.now()
        setRecommendations(data)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [timeframe])

  useEffect(() => {
    fetchRecommendations()
  }, [fetchRecommendations])

  const invalidateCache = useCallback(() => {
    recommendationCache = {
      short_term: null,
      long_term: null,
      timestamp: 0
    }
  }, [])

  return { recommendations, loading, error, invalidateCache }
}
