import { createContext, useContext, useState, useEffect, useCallback } from 'react'

const PortfolioContext = createContext(null)

export function PortfolioProvider({ children }) {
  const [hasPortfolio, setHasPortfolio] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [ltRecommendations, setLtRecommendations] = useState(null)
  const [stRecommendations, setStRecommendations] = useState(null)
  const [loading, setLoading] = useState(true)

  const reload = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/portfolio/full')
      if (!res.ok) return
      const data = await res.json()
      setHasPortfolio(data.has_portfolio || false)
      setAnalysis(data.analysis || null)
      setLtRecommendations(data.long_term || null)
      setStRecommendations(data.short_term || null)
    } catch {
      // no portfolio is a valid state — stay with defaults
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { reload() }, [reload])

  return (
    <PortfolioContext.Provider value={{
      hasPortfolio,
      analysis,
      ltRecommendations,
      stRecommendations,
      loading,
      reload,
    }}>
      {children}
    </PortfolioContext.Provider>
  )
}

export function usePortfolio() {
  return useContext(PortfolioContext)
}
