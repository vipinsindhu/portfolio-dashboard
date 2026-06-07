import { useState, useCallback } from 'react'
import './PortfolioInput.css'

function PortfolioInput({ onPortfolioLoaded, onAnalyze }) {
  const [holdings, setHoldings] = useState([])
  const [manualInput, setManualInput] = useState({
    symbol: '',
    quantity: '',
    purchase_price: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

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
        console.log('Adding holdings to preview table:', data.holdings_list)
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
        console.log('Updated holdings state:', stats.holdings)
        setHoldings(stats.holdings)
      } else {
        console.warn('No holdings_list in response or empty:', data.holdings_list)
      }

      setSuccess(`✅ Loaded ${data.holdings} holdings from CSV`)

      // Reset file input
      event.target.value = ''

      // Trigger portfolio loaded callback
      if (onPortfolioLoaded) {
        onPortfolioLoaded()
      }
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

      // Reset form
      setManualInput({ symbol: '', quantity: '', purchase_price: '' })

      // Trigger portfolio loaded callback
      if (onPortfolioLoaded) {
        onPortfolioLoaded()
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRemoveHolding = (index) => {
    const newHoldings = holdings.filter((_, i) => i !== index)
    const stats = calculatePortfolioStats(newHoldings)
    setHoldings(stats.holdings)
    setSuccess(null)
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

      {/* Input Methods - Side by Side */}
      <div className="input-methods-grid">
        {/* CSV Upload */}
        <div className="input-method csv-upload">
          <h4>📤 Upload CSV</h4>
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
              <p className="upload-hint">Format: Symbol, Quantity, PurchasePrice</p>
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

        {/* Manual Entry */}
        <form className="input-method manual-entry" onSubmit={handleManualAdd}>
          <h4>➕ Add One Stock</h4>

          <div className="form-group">
            <label htmlFor="symbol">Stock Symbol</label>
            <input
              id="symbol"
              type="text"
              placeholder="e.g., AAPL"
              value={manualInput.symbol}
              onChange={(e) =>
                setManualInput({ ...manualInput, symbol: e.target.value.toUpperCase() })
              }
              disabled={loading}
              maxLength="5"
            />
          </div>

          <div className="form-group">
            <label htmlFor="quantity">Quantity</label>
            <input
              id="quantity"
              type="number"
              placeholder="e.g., 10"
              value={manualInput.quantity}
              onChange={(e) => setManualInput({ ...manualInput, quantity: e.target.value })}
              disabled={loading}
              step="0.01"
              min="0"
            />
          </div>

          <div className="form-group">
            <label htmlFor="purchase-price">Purchase Price ($)</label>
            <input
              id="purchase-price"
              type="number"
              placeholder="e.g., 150.00"
              value={manualInput.purchase_price}
              onChange={(e) =>
                setManualInput({ ...manualInput, purchase_price: e.target.value })
              }
              disabled={loading}
              step="0.01"
              min="0"
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Adding...' : '➕ Add'}
          </button>
        </form>
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

      {/* Empty State */}
      {holdings.length === 0 && (
        <div className="input-footer">
          <p className="footer-hint">
            💡 Start by uploading a CSV or adding your first stock
          </p>
        </div>
      )}
    </div>
  )
}

export default PortfolioInput
