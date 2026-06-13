import { useState, useCallback, useEffect, useRef } from 'react'
import { usePortfolio } from '../../../context/PortfolioContext'
import './PortfolioInput.css'

// Deliberately tech-heavy (~60%) so the demo analysis surfaces concentration warnings
const SAMPLE_PORTFOLIO = [
  { symbol: 'AAPL', quantity: 10, purchase_price: 180 },
  { symbol: 'MSFT', quantity: 6, purchase_price: 410 },
  { symbol: 'NVDA', quantity: 30, purchase_price: 120 },
  { symbol: 'JPM', quantity: 12, purchase_price: 195 },
  { symbol: 'XOM', quantity: 15, purchase_price: 110 },
  { symbol: 'BND', quantity: 20, purchase_price: 73 }
]

function PortfolioInput({ autoLoadSample, onAutoLoadHandled }) {
  const { updateHoldings } = usePortfolio()
  const [holdings, setHoldings] = useState([])
  const [manualInput, setManualInput] = useState({
    symbol: '',
    quantity: '',
    purchase_price: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [expandedSection, setExpandedSection] = useState(null)

  const calculatePortfolioStats = useCallback((holdingsList) => {
    const totalCost = holdingsList.reduce((sum, h) => sum + h.total_cost, 0)
    return {
      totalCost,
      holdings: holdingsList.map(h => ({
        ...h,
        percentage: totalCost > 0 ? ((h.total_cost / totalCost) * 100).toFixed(1) : 0
      }))
    }
  }, [])

  const handleCSVUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    console.log('CSV Upload started:', file.name)
    setLoading(true)
    setError(null)
    setSuccess(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('/api/portfolio/upload', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Upload failed')
      }

      const data = await response.json()
      console.log('CSV Upload Response:', data)

      // Add CSV holdings to preview table
      if (data.holdings_list && data.holdings_list.length > 0) {
        const newHoldings = [
          ...holdings,
          ...data.holdings_list.map(h => ({
            symbol: h.symbol,
            quantity: h.quantity,
            purchase_price: h.purchase_price,
            total_cost: h.total_cost,
            percentage: 0
          }))
        ]
        const stats = calculatePortfolioStats(newHoldings)
        setHoldings(stats.holdings)
        updateHoldings(stats.holdings)
      } else {
        console.warn('No holdings_list in response or empty:', data.holdings_list)
      }

      setSuccess(`Loaded ${data.holdings} stocks`)

      // Reset file input
      event.target.value = ''
    } catch (err) {
      console.error('CSV Upload Error:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleManualAdd = async (e) => {
    e.preventDefault()

    if (!manualInput.symbol || !manualInput.quantity || !manualInput.purchase_price) {
      setError('Please fill in all fields')
      return
    }

    setLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await fetch('/api/portfolio/add-holding', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: manualInput.symbol.toUpperCase(),
          quantity: parseFloat(manualInput.quantity),
          purchase_price: parseFloat(manualInput.purchase_price),
          current_price: parseFloat(manualInput.purchase_price)
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to add holding')
      }

      // Add to local holdings
      const newHolding = {
        symbol: manualInput.symbol.toUpperCase(),
        quantity: parseFloat(manualInput.quantity),
        purchase_price: parseFloat(manualInput.purchase_price),
        total_cost: parseFloat(manualInput.quantity) * parseFloat(manualInput.purchase_price),
        percentage: 0
      }

      const newHoldings = [...holdings, newHolding]
      const stats = calculatePortfolioStats(newHoldings)
      setHoldings(stats.holdings)
      setSuccess(`✅ Added ${manualInput.symbol}`)
      setManualInput({ symbol: '', quantity: '', purchase_price: '' })
      updateHoldings(stats.holdings)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleLoadSample = useCallback(async () => {
    setLoading(true)
    setError(null)
    setSuccess(null)

    // Upload replaces the server-side portfolio, so repeat clicks stay idempotent
    const csv =
      'Symbol,Quantity,PurchasePrice\n' +
      SAMPLE_PORTFOLIO.map(h => `${h.symbol},${h.quantity},${h.purchase_price}`).join('\n')
    const formData = new FormData()
    formData.append('file', new File([csv], 'sample_portfolio.csv', { type: 'text/csv' }))

    try {
      const response = await fetch('/api/portfolio/upload', {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to load sample portfolio')
      }

      const data = await response.json()
      const stats = calculatePortfolioStats(
        (data.holdings_list || []).map(h => ({ ...h, percentage: 0 }))
      )
      setHoldings(stats.holdings)
      setSuccess(`✨ Loaded sample portfolio (${data.holdings} holdings) — analyzing...`)
      updateHoldings(stats.holdings)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [calculatePortfolioStats, onPortfolioLoaded, onAnalyze])

  // Auto-load the sample when arriving via the Welcome page's "Try a Demo" CTA
  const autoLoadTriggered = useRef(false)
  useEffect(() => {
    if (autoLoadSample && !autoLoadTriggered.current) {
      autoLoadTriggered.current = true
      handleLoadSample()
      if (onAutoLoadHandled) {
        onAutoLoadHandled()
      }
    }
  }, [autoLoadSample, handleLoadSample, onAutoLoadHandled])

  const handleRemoveHolding = (index) => {
    const newHoldings = holdings.filter((_, i) => i !== index)
    const stats = calculatePortfolioStats(newHoldings)
    setHoldings(stats.holdings)
    setSuccess(null)
    updateHoldings(stats.holdings)
  }

  const downloadCSVTemplate = () => {
    const template = 'Symbol,Quantity,PurchasePrice\nAAPL,10,150\nMSFT,5,350\n'
    const element = document.createElement('a')
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(template))
    element.setAttribute('download', 'portfolio_template.csv')
    element.style.display = 'none'
    document.body.appendChild(element)
    element.click()
    document.body.removeChild(element)
  }

  const totalPortfolioCost = holdings.reduce((sum, h) => sum + h.total_cost, 0)

  return (
    <div className="portfolio-input-container">
      <div className="input-header">
        <h3>Add Your Holdings</h3>
        <p>Use CSV for multiple stocks, or add them one at a time</p>
      </div>

      {error && <div className="input-error">{error}</div>}
      {success && <div className="input-success">{success}</div>}

      {/* Empty State Hint */}
      {holdings.length === 0 && (
        <div className="input-intro">
          <p>💡 Start by uploading a CSV or adding your first stock</p>
          <button
            type="button"
            className="btn-sample-portfolio"
            onClick={handleLoadSample}
            disabled={loading}
          >
            {loading ? '⏳ Loading...' : '✨ No stocks handy? Try a sample portfolio'}
          </button>
        </div>
      )}

      {/* Input Methods - Collapsible */}
      <div className="input-methods-collapsible">
        {/* CSV Upload Section */}
        <div className={`collapsible-section ${expandedSection === 'csv' ? 'expanded' : 'collapsed'}`}>
          <button
            type="button"
            className="section-header"
            onClick={() => setExpandedSection(expandedSection === 'csv' ? null : 'csv')}
          >
            <span className="arrow">{expandedSection === 'csv' ? '▼' : '▶'}</span>
            <span className="title">📤 Upload CSV</span>
            <span className="description">Load multiple holdings at once</span>
          </button>

          {expandedSection === 'csv' && (
            <div className="section-content">
              <div className="upload-zone">
                <input
                  type="file"
                  id="csv-file"
                  accept=".csv"
                  onChange={handleCSVUpload}
                  disabled={loading}
                  className="file-input"
                />
                <label htmlFor="csv-file" className="upload-label">
                  <div className="upload-icon">📁</div>
                  <p className="upload-text">Drag CSV here or click to select</p>
                  <p className="upload-hint">Format: Symbol, Quantity, Cost Basis (or PurchasePrice)</p>
                </label>
              </div>

              <button
                type="button"
                className="btn-secondary"
                onClick={downloadCSVTemplate}
                disabled={loading}
              >
                📥 Download Template
              </button>
            </div>
          )}
        </div>

        {/* Manual Entry Section */}
        <div className={`collapsible-section ${expandedSection === 'manual' ? 'expanded' : 'collapsed'}`}>
          <button
            type="button"
            className="section-header"
            onClick={() => setExpandedSection(expandedSection === 'manual' ? null : 'manual')}
          >
            <span className="arrow">{expandedSection === 'manual' ? '▼' : '▶'}</span>
            <span className="title">➕ Add stocks manually</span>
            <span className="description">Add holdings one at a time</span>
          </button>

          {expandedSection === 'manual' && (
            <form className="manual-form" onSubmit={handleManualAdd}>
              <div className="form-columns">
                <div className="form-group column">
                  <label htmlFor="symbol">Symbol</label>
                  <input
                    id="symbol"
                    type="text"
                    placeholder="AAPL"
                    value={manualInput.symbol}
                    onChange={(e) =>
                      setManualInput({ ...manualInput, symbol: e.target.value.toUpperCase() })
                    }
                    disabled={loading}
                    maxLength="5"
                  />
                </div>

                <div className="form-group column">
                  <label htmlFor="quantity">Quantity</label>
                  <input
                    id="quantity"
                    type="number"
                    placeholder="10"
                    value={manualInput.quantity}
                    onChange={(e) => setManualInput({ ...manualInput, quantity: e.target.value })}
                    disabled={loading}
                    step="0.01"
                    min="0"
                  />
                </div>

                <div className="form-group column">
                  <label htmlFor="purchase-price">Purchase Price</label>
                  <input
                    id="purchase-price"
                    type="number"
                    placeholder="150.00"
                    value={manualInput.purchase_price}
                    onChange={(e) =>
                      setManualInput({ ...manualInput, purchase_price: e.target.value })
                    }
                    disabled={loading}
                    step="0.01"
                    min="0"
                  />
                </div>

                <button type="submit" className="btn-add" disabled={loading}>
                  {loading ? 'Adding...' : '➕'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>

      {/* Portfolio Summary Table */}
      {holdings.length > 0 && (
        <div className="portfolio-table-container">
          <h4>Your Holdings ({holdings.length})</h4>
          <div className="portfolio-table-wrapper">
            <table className="portfolio-table">
              <thead>
                <tr>
                  <th>Symbol</th>
                  <th>Quantity</th>
                  <th>Price</th>
                  <th>Total Cost</th>
                  <th>% of Portfolio</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {holdings.map((holding, idx) => (
                  <tr key={idx}>
                    <td className="symbol-cell"><strong>{holding.symbol}</strong></td>
                    <td>{holding.quantity}</td>
                    <td>${holding.purchase_price.toFixed(2)}</td>
                    <td>${holding.total_cost.toFixed(2)}</td>
                    <td>{holding.percentage}%</td>
                    <td>
                      <button
                        type="button"
                        className="btn-remove"
                        onClick={() => handleRemoveHolding(idx)}
                        disabled={loading}
                        title="Remove this holding"
                      >
                        ✕
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr>
                  <td colSpan="3"><strong>Total Portfolio</strong></td>
                  <td><strong>${totalPortfolioCost.toFixed(2)}</strong></td>
                  <td><strong>100%</strong></td>
                  <td></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}

    </div>
  )
}

export default PortfolioInput
