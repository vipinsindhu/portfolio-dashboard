import { useState } from 'react'
import './PortfolioInput.css'

function PortfolioInput({ onPortfolioLoaded, onAnalyze }) {
  const [uploadMethod, setUploadMethod] = useState('csv') // 'csv' or 'manual'
  const [csvFile, setCsvFile] = useState(null)
  const [manualInput, setManualInput] = useState({
    symbol: '',
    quantity: '',
    purchase_price: ''
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const handleCSVUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

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
      setSuccess(`✅ Loaded ${data.holdings} holdings`)
      setCsvFile(null)

      // Trigger analysis
      if (onPortfolioLoaded) {
        onPortfolioLoaded()
      }

      // Auto-analyze after short delay
      setTimeout(() => {
        if (onAnalyze) onAnalyze()
      }, 500)
    } catch (err) {
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

      const data = await response.json()
      setSuccess(`✅ Added ${manualInput.symbol}`)

      // Reset form
      setManualInput({ symbol: '', quantity: '', purchase_price: '' })

      // Trigger analysis
      if (onPortfolioLoaded) {
        onPortfolioLoaded()
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
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

  return (
    <div className="portfolio-input-container">
      <div className="input-header">
        <h3>Upload Your Portfolio</h3>
        <p>Add your holdings to get personalized analysis</p>
      </div>

      {error && <div className="input-error">{error}</div>}
      {success && <div className="input-success">{success}</div>}

      {/* Method Tabs */}
      <div className="input-method-tabs">
        <button
          className={`method-tab ${uploadMethod === 'csv' ? 'active' : ''}`}
          onClick={() => setUploadMethod('csv')}
          disabled={loading}
        >
          📤 CSV Upload
        </button>
        <button
          className={`method-tab ${uploadMethod === 'manual' ? 'active' : ''}`}
          onClick={() => setUploadMethod('manual')}
          disabled={loading}
        >
          ➕ Manual Entry
        </button>
      </div>

      {/* CSV Upload */}
      {uploadMethod === 'csv' && (
        <div className="input-method csv-upload">
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
      )}

      {/* Manual Entry */}
      {uploadMethod === 'manual' && (
        <form className="input-method manual-entry" onSubmit={handleManualAdd}>
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
            {loading ? 'Adding...' : '➕ Add Holding'}
          </button>
        </form>
      )}

      <div className="input-footer">
        <p className="footer-hint">
          💡 Add multiple holdings one at a time, or use CSV for faster upload
        </p>
      </div>
    </div>
  )
}

export default PortfolioInput
