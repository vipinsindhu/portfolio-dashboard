import { useState, useEffect } from 'react'
import Header from './components/Header'
import TabBar from './components/TabBar'
import Research from './components/Research'
import SignalList from './components/SignalList'
import SignalArchive from './components/SignalArchive'
import MacroTab from './components/MacroTab'

function App() {
  const [signals, setSignals] = useState(null)
  const [macroData, setMacroData] = useState(null)
  const [activeTab, setActiveTab] = useState('research')
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState(null)

  const fetchSignals = async () => {
    try {
      const response = await fetch('/api/signals')
      if (!response.ok) throw new Error('Failed to fetch signals')
      const data = await response.json()
      setSignals(data)
      setError(null)
    } catch (err) {
      console.error('Error fetching signals:', err)
      setError(err.message)
    }
  }

  const fetchMacro = async () => {
    try {
      const response = await fetch('/api/macro')
      if (!response.ok) throw new Error('Failed to fetch macro data')
      const data = await response.json()
      setMacroData(data)
    } catch (err) {
      console.error('Error fetching macro:', err)
    }
  }

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await Promise.all([fetchSignals(), fetchMacro()])
      setError(null)
    } catch (err) {
      console.error('Error refreshing:', err)
      setError(err.message)
    } finally {
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchSignals()
    fetchMacro()
  }, [])

  if (!signals) {
    return <div className="content">Loading signals...</div>
  }

  return (
    <>
      <Header
        lastUpdated={signals.generated_at}
        onRefresh={handleRefresh}
        refreshing={refreshing}
      />
      <TabBar activeTab={activeTab} onTabChange={setActiveTab} />
      <div className="content">
        {activeTab === 'research' && (
          <div className="panel active" id="tab-research">
            <Research />
          </div>
        )}
        {activeTab === 'signals' && (
          <div className="panel active" id="tab-signals">
            <SignalList signals={signals.data} />
          </div>
        )}
        {activeTab === 'archive' && (
          <div className="panel active" id="tab-archive">
            <SignalArchive />
          </div>
        )}
        {activeTab === 'macro' && macroData && (
          <div className="panel active" id="tab-macro">
            <MacroTab signals={macroData.macro_signals} />
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
