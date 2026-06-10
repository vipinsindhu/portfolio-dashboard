import { useState } from 'react'
import Header from './components/Header'
import Learn from './components/tabs/Learn/Learn'
import Analyse from './components/tabs/Analyse/Analyse'
import ShortTerm from './components/tabs/ShortTerm/ShortTerm'
import LongTerm from './components/tabs/LongTerm/LongTerm'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('learn')

  return (
    <>
      <Header />

      <div className="tab-bar">
        <button
          className={`tab-button ${activeTab === 'learn' ? 'active' : ''}`}
          onClick={() => setActiveTab('learn')}
        >
          📚 Learn
        </button>
        <button
          className={`tab-button ${activeTab === 'analyse' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyse')}
        >
          📊 My Stocks
        </button>
        <button
          className={`tab-button ${activeTab === 'short-term' ? 'active' : ''}`}
          onClick={() => setActiveTab('short-term')}
        >
          💡 This Week
        </button>
        <button
          className={`tab-button ${activeTab === 'long-term' ? 'active' : ''}`}
          onClick={() => setActiveTab('long-term')}
        >
          🎯 Build Wealth
        </button>
      </div>

      <div className="app-content">
        {activeTab === 'learn' && <Learn />}
        {activeTab === 'analyse' && <Analyse />}
        {activeTab === 'short-term' && <ShortTerm />}
        {activeTab === 'long-term' && <LongTerm />}
      </div>
    </>
  )
}

export default App
