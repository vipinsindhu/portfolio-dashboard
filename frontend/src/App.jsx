import { useState } from 'react'
import Header from './components/Header'
import Disclaimer from './components/Disclaimer'
import Welcome from './components/tabs/Welcome/Welcome'
import Learn from './components/tabs/Learn/Learn'
import Analyse from './components/tabs/Analyse/Analyse'
import ShortTerm from './components/tabs/ShortTerm/ShortTerm'
import LongTerm from './components/tabs/LongTerm/LongTerm'
import FeedbackForm from './components/FeedbackForm'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('welcome')
  const [showFeedback, setShowFeedback] = useState(false)

  return (
    <>
      <Header />

      <div className="app-container">
        <Disclaimer />
      </div>

      <div className="tab-bar">
        <button
          className={`tab-button ${activeTab === 'welcome' ? 'active' : ''}`}
          onClick={() => setActiveTab('welcome')}
        >
          🏠 Home
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
        <button
          className={`tab-button ${activeTab === 'analyse' ? 'active' : ''}`}
          onClick={() => setActiveTab('analyse')}
        >
          📊 My Stocks
        </button>
        <button
          className={`tab-button ${activeTab === 'learn' ? 'active' : ''}`}
          onClick={() => setActiveTab('learn')}
        >
          📚 Learn
        </button>
      </div>

      <div className="app-content">
        {activeTab === 'welcome' && (
          <Welcome onTabChange={setActiveTab} onFeedback={() => setShowFeedback(true)} />
        )}
        {activeTab === 'short-term' && <ShortTerm />}
        {activeTab === 'long-term' && <LongTerm />}
        {activeTab === 'analyse' && <Analyse />}
        {activeTab === 'learn' && <Learn />}
      </div>

      {showFeedback && (
        <FeedbackForm onClose={() => setShowFeedback(false)} />
      )}
    </>
  )
}

export default App
