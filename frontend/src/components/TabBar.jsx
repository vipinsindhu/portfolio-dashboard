function TabBar({ activeTab, onTabChange }) {
  return (
    <div className="tabs">
      <button
        className={`tab ${activeTab === 'research' ? 'active' : ''}`}
        onClick={() => onTabChange('research')}
      >
        Research
      </button>
      <button
        className={`tab ${activeTab === 'signals' ? 'active' : ''}`}
        onClick={() => onTabChange('signals')}
      >
        This Week's Signals
      </button>
      <button
        className={`tab ${activeTab === 'archive' ? 'active' : ''}`}
        onClick={() => onTabChange('archive')}
      >
        Signal Archive
      </button>
      <button
        className={`tab ${activeTab === 'macro' ? 'active' : ''}`}
        onClick={() => onTabChange('macro')}
      >
        Macro Context
      </button>
    </div>
  )
}

export default TabBar
