import { useState, useEffect } from 'react'
import Header from './components/Header'
import TabBar from './components/TabBar'
import Research from './components/Research'
import SignalList from './components/SignalList'
import SignalArchive from './components/SignalArchive'

function App() {
  const [signals, setSignals] = useState(null)
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

  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      await fetchSignals()
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
