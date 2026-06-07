import { useState, useEffect } from 'react'
import './Research.css'

function ResearchWatchlist({ onSelectStock }) {
  const [watchlist, setWatchlist] = useState([])
  const [search, setSearch] = useState('')
  const [stockPrices, setStockPrices] = useState({})
  const [loading, setLoading] = useState(false)

  // Load watchlist from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('watchlist')
    if (saved) {
      setWatchlist(JSON.parse(saved))
    }
  }, [])

  // Save watchlist to localStorage
  const saveWatchlist = (newWatchlist) => {
    setWatchlist(newWatchlist)
    localStorage.setItem('watchlist', JSON.stringify(newWatchlist))
  }

  const addStock = async () => {
    const ticker = search.toUpperCase().trim()
    if (!ticker || watchlist.find(s => s.ticker === ticker)) {
      setSearch('')
      return
    }

    try {
      setLoading(true)
      // Fetch stock data from backend
      const response = await fetch(`/api/stock/${ticker}`)
      if (response.ok) {
        const data = await response.json()
        const newStock = {
          ticker,
          company: data.company_name || ticker,
          sector: data.sector || 'Unknown',
          price: data.current_price || 0,
          change: data.change_pct || 0,
          addedAt: new Date().toISOString()
        }
        saveWatchlist([newStock, ...watchlist])
        setSearch('')
      }
    } catch (err) {
      console.error('Error adding stock:', err)
    } finally {
      setLoading(false)
    }
  }

  const removeStock = (ticker) => {
    saveWatchlist(watchlist.filter(s => s.ticker !== ticker))
  }

  const handleAddClick = () => {
    if (search.trim()) addStock()
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleAddClick()
    }
  }

  const formatDate = (isoString) => {
    const date = new Date(isoString)
    const now = new Date()
    const diffDays = Math.floor((now - date) / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return 'Today'
    if (diffDays === 1) return 'Yesterday'
    if (diffDays < 7) return `${diffDays} days ago`
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
    return `${Math.floor(diffDays / 30)} months ago`
  }

  return (
    <div className="research-container">
      <div className="watchlist-section">
        <div className="watchlist-header">
          <h2>Research Watchlist</h2>
          <p>Build your stock research list</p>
        </div>

        <div style={{ marginBottom: '32px' }}>
          <input
            type="text"
            className="search-input"
            placeholder="Search stocks by ticker or name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <button
            className="research-btn"
            onClick={handleAddClick}
            disabled={loading || !search.trim()}
            style={{ marginLeft: '8px' }}
          >
            {loading ? 'Adding...' : 'Add to Watchlist'}
          </button>
        </div>

        {watchlist.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '60px 20px',
            color: 'var(--text-secondary)'
          }}>
            <p style={{ fontSize: '16px', marginBottom: '8px' }}>No stocks in your watchlist yet</p>
            <p style={{ fontSize: '13px' }}>Add a ticker above to start researching</p>
          </div>
        ) : (
          <div className="watchlist-grid">
            {watchlist.map((stock) => (
              <div key={stock.ticker} className="stock-card">
                <div className="stock-header">
                  <div className="stock-ticker">{stock.ticker}</div>
                  <div className="stock-price">${stock.price?.toFixed(2) || 'N/A'}</div>
                </div>
                <div className="stock-company">{stock.company}</div>
                <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                  {stock.sector}
                </div>
                <div className="stock-meta">
                  <span style={{ fontSize: '12px' }}>
                    Added {formatDate(stock.addedAt)}
                  </span>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button
                      className="research-btn"
                      onClick={() => onSelectStock(stock.ticker)}
                      style={{ padding: '6px 12px', fontSize: '11px' }}
                    >
                      Research
                    </button>
                    <button
                      style={{
                        padding: '6px 8px',
                        background: 'transparent',
                        border: '1px solid var(--border-light)',
                        color: 'var(--text-secondary)',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '12px'
                      }}
                      onClick={() => removeStock(stock.ticker)}
                      title="Remove from watchlist"
                    >
                      ✕
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

export default ResearchWatchlist
