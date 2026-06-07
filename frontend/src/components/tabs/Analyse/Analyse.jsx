import { useState, useCallback } from 'react'
import PortfolioInput from './PortfolioInput'
import PitfallDetector from './PitfallDetector'
import './Analyse.css'

function Analyse() {
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [portfolioLoaded, setPortfolioLoaded] = useState(false)

  const handleAnalyze = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/portfolio/analysis')

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || errorData.message || 'Analysis failed')
      }

      const data = await response.json()
      setAnalysis(data)
      setPortfolioLoaded(true)
    } catch (err) {
      setError(err.message)
      console.error('Error analyzing portfolio:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  const handlePortfolioLoaded = () => {
    setPortfolioLoaded(true)
    // Analysis will be triggered after upload completes
  }

  return (
    <div className="analyse-container">
      <div className="analyse-header">
        <h2>📊 Analyse Your Portfolio</h2>
        <p>Upload your portfolio to get a detailed analysis of potential risks and pitfalls</p>
      </div>

      {error && <div className="error-message">{error}</div>}

      {/* Portfolio Input */}
      <PortfolioInput onPortfolioLoaded={handlePortfolioLoaded} onAnalyze={handleAnalyze} />

      {/* Manual Analyze Button */}
      {portfolioLoaded && (
        <div className="manual-analyze-section">
          <button className="btn-primary btn-large" onClick={handleAnalyze} disabled={loading}>
            {loading ? '⏳ Analyzing...' : '🔍 Analyze Portfolio'}
          </button>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="loading-message">
          <p>Analyzing your portfolio...</p>
        </div>
      )}

      {/* Analysis Results */}
      {analysis && <PitfallDetector analysis={analysis} />}

      {/* Empty State */}
      {!portfolioLoaded && !analysis && (
        <div className="empty-state">
          <div className="empty-state-content">
            <div className="empty-icon">📁</div>
            <h3>No Portfolio Yet</h3>
            <p>Upload a CSV file or add holdings manually to get started</p>
          </div>
        </div>
      )}
    </div>
  )
}

export default Analyse
