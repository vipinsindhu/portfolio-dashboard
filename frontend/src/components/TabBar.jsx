function TabBar({ activeTab, onTabChange }) {
  return (
    <div className="tabs">
      <button
        className={`tab ${activeTab === 'macro' ? 'active' : ''}`}
        onClick={() => onTabChange('macro')}
      >
        Macro
      </button>
      <button
        className={`tab ${activeTab === 'analysis' ? 'active' : ''}`}
        onClick={() => onTabChange('analysis')}
      >
        Analysis
      </button>
      <button
        className={`tab ${activeTab === 'outlook' ? 'active' : ''}`}
        onClick={() => onTabChange('outlook')}
      >
        Outlook
      </button>
      <button
        className={`tab ${activeTab === 'portfolio' ? 'active' : ''}`}
        onClick={() => onTabChange('portfolio')}
      >
        Portfolio
      </button>
      <button
        className={`tab ${activeTab === 'invest' ? 'active' : ''}`}
        onClick={() => onTabChange('invest')}
      >
        Investment Plan
      </button>
    </div>
  )
}

export default TabBar
