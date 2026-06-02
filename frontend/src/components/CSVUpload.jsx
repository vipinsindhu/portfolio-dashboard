import { useRef } from 'react'

function CSVUpload({ onDataLoaded }) {
  const fileInputRef = useRef(null)

  const handleFileUpload = (e) => {
    const file = e.target.files[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      try {
        const csv = event.target.result
        const lines = csv.trim().split('\n')

        if (lines.length < 2) {
          alert('CSV must have at least a header row and data row')
          return
        }

        const headers = lines[0].split(',').map(h => h.trim().toLowerCase())
        const holdings = []

        for (let i = 1; i < lines.length; i++) {
          const values = lines[i].split(',').map(v => v.trim())
          if (values.length < 3 || !values[0]) continue

          const holding = {
            id: `csv-${Date.now()}-${i}`,
            ticker: values[0].toUpperCase(),
            shares: parseFloat(values[1]) || 0,
            costBasis: parseFloat(values[2]) || 0,
          }

          if (holding.ticker && holding.shares > 0 && holding.costBasis > 0) {
            holdings.push(holding)
          }
        }

        if (holdings.length === 0) {
          alert('No valid holdings found in CSV')
          return
        }

        onDataLoaded(holdings)
        alert(`Loaded ${holdings.length} holdings from CSV`)
        fileInputRef.current.value = ''
      } catch (error) {
        alert(`Error parsing CSV: ${error.message}`)
      }
    }
    reader.readAsText(file)
  }

  return (
    <div style={{ marginBottom: '20px' }}>
      <label htmlFor="csv-upload">Upload CSV File</label>
      <input
        id="csv-upload"
        type="file"
        accept=".csv"
        ref={fileInputRef}
        onChange={handleFileUpload}
        style={{
          width: '100%',
          padding: '10px',
          background: 'var(--surface2)',
          border: '1px solid var(--border)',
          color: 'var(--text)',
          borderRadius: '6px',
          marginBottom: '12px',
          cursor: 'pointer',
        }}
      />
      <div
        style={{
          fontSize: '10px',
          color: 'var(--muted)',
          padding: '12px',
          background: 'var(--surface2)',
          borderRadius: '6px',
          lineHeight: '1.6',
        }}
      >
        <strong>CSV Format:</strong><br />
        Ticker,Shares,CostBasis<br />
        AAPL,100,150.50<br />
        MSFT,50,350.00<br />
        BND,200,80.00
      </div>
    </div>
  )
}

export default CSVUpload
