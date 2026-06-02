import { useState, useEffect } from 'react'
import Header from './components/Header'
import TabBar from './components/TabBar'
import MacroTab from './components/MacroTab'
import OutlookTab from './components/OutlookTab'
import PortfolioTab from './components/PortfolioTab'
import InvestmentPlanTab from './components/InvestmentPlanTab'

function App() {
  const [macroData, setMacroData] = useState(null)
  const [activeTab, setActiveTab] = useState('macro')
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)
  const [holdings, setHoldings] = useState([])

  const fetchMacro = async () => {
    try {
      const response = await fetch('/api/macro')
      if (!response.ok) throw new Error('Failed to fetch macro data')
      const data = await response.json()
      setMacroData(data)
      setError(null)
    } catch (err) {
      console.error('Error fetching macro:', err)
      setError(err.message)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      const response = await fetch('/api/refresh', { method: 'POST' })
      if (!response.ok) throw new Error('Failed to refresh')
      const data = await response.json()
      setMacroData(data)
      setError(null)
    } catch (err) {
      console.error('Error refreshing:', err)
      setError(err.message)
    } finally {
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchMacro()
  }, [])

  if (!macroData) {
    return <div className="content">Loading...</div>
  }

  return (
    <>
      <Header
        lastUpdated={macroData.last_updated}
        onRefresh={handleRefresh}
        refreshing={refreshing}
      />
      <TabBar activeTab={activeTab} onTabChange={setActiveTab} />
      <div className="content">
        {activeTab === 'macro' && (
          <div className="panel active" id="tab-macro">
            <MacroTab signals={macroData.macro_signals} />
          </div>
        )}
        {activeTab === 'outlook' && (
          <div className="panel active" id="tab-outlook">
            <OutlookTab signals={macroData.macro_signals} />
          </div>
        )}
        {activeTab === 'portfolio' && (
          <div className="panel active" id="tab-portfolio">
            <PortfolioTab holdings={holdings} onHoldingsChange={setHoldings} />
          </div>
        )}
        {activeTab === 'invest' && (
          <div className="panel active" id="tab-invest">
            <InvestmentPlanTab signals={macroData.macro_signals} holdings={holdings} />
          </div>
        )}
      </div>
      {error && (
        <div style={{ color: 'var(--red)', padding: '16px 32px' }}>
          Error: {error}
        </div>
      )}
    </>
  )
}

export default App
