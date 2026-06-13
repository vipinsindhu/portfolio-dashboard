import { createContext, useContext, useState, useCallback } from 'react'

const PortfolioContext = createContext(null)

export function PortfolioProvider({ children }) {
  const [holdings, setHoldings] = useState([])
  const [hasPortfolio, setHasPortfolio] = useState(false)
  const [analysis, setAnalysis] = useState(null)
  const [ltRecommendations, setLtRecommendations] = useState(null)
  const [stRecommendations, setStRecommendations] = useState(null)
  const [loading, setLoading] = useState(false)

  const fetchPortfolioFull = useCallback(async (holdingsList) => {
    if (!holdingsList || holdingsList.length === 0) {
      setHasPortfolio(false)
      setAnalysis(null)
      setLtRecommendations(null)
      setStRecommendations(null)
      return
    }
    setLoading(true)
    try {
      const res = await fetch('/api/portfolio/full', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ holdings: holdingsList }),
      })
      if (!res.ok) return
      const data = await res.json()
      setHasPortfolio(data.has_portfolio || false)
      setAnalysis(data.analysis || null)
      setLtRecommendations(data.long_term || null)
      setStRecommendations(data.short_term || null)
    } catch {
      // portfolio is optional — stay with current state
    } finally {
      setLoading(false)
    }
  }, [])

  // reload() re-runs analysis against the holdings already in state
  const reload = useCallback(() => fetchPortfolioFull(holdings), [holdings, fetchPortfolioFull])

  // updateHoldings() is called by PortfolioInput whenever the list changes
  const updateHoldings = useCallback((newHoldings) => {
    setHoldings(newHoldings)
    fetchPortfolioFull(newHoldings)
  }, [fetchPortfolioFull])

  return (
    <PortfolioContext.Provider value={{
      hasPortfolio,
      analysis,
      ltRecommendations,
      stRecommendations,
      loading,
      reload,
      updateHoldings,
    }}>
      {children}
    </PortfolioContext.Provider>
  )
}

export function usePortfolio() {
  return useContext(PortfolioContext)
}
