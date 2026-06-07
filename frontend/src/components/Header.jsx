function Header({ lastUpdated, onRefresh, refreshing }) {
  const formatDate = (isoString) => {
    if (!isoString) return 'Unknown'
    const date = new Date(isoString)
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'UTC',
    })
  }

  return (
    <div className="header">
      <h1>Portfolio Builder</h1>
      <p>Macro Indicators · Market Outlook · Signals auto-generated hourly · Last Updated {formatDate(lastUpdated)}</p>
      <div className="header-right">
        <button
          className="refresh-btn"
          onClick={onRefresh}
          disabled={refreshing}
        >
          {refreshing ? 'Refreshing...' : 'Refresh Now'}
        </button>
      </div>
    </div>
  )
}

export default Header
