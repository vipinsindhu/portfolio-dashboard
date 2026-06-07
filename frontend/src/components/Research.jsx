import { useState } from 'react'
import ResearchWatchlist from './ResearchWatchlist'
import ResearchDetail from './ResearchDetail'
import RecommendationView from './RecommendationView'

function Research() {
  const [view, setView] = useState('watchlist') // 'watchlist', 'detail', 'recommendation'
  const [selectedTicker, setSelectedTicker] = useState(null)

  const handleSelectStock = (ticker) => {
    setSelectedTicker(ticker)
    setView('detail')
  }

  const handleBackFromDetail = () => {
    setView('watchlist')
    setSelectedTicker(null)
  }

  const handleRecommendation = (ticker) => {
    setSelectedTicker(ticker)
    setView('recommendation')
  }

  const handleBackFromRecommendation = () => {
    setView('detail')
  }

  if (view === 'watchlist') {
    return <ResearchWatchlist onSelectStock={handleSelectStock} />
  }

  if (view === 'detail' && selectedTicker) {
    return (
      <ResearchDetail
        ticker={selectedTicker}
        onBack={handleBackFromDetail}
        onRecommendation={handleRecommendation}
      />
    )
  }

  if (view === 'recommendation' && selectedTicker) {
    return (
      <RecommendationView
        ticker={selectedTicker}
        onBack={handleBackFromRecommendation}
      />
    )
  }

  return <ResearchWatchlist onSelectStock={handleSelectStock} />
}

export default Research
