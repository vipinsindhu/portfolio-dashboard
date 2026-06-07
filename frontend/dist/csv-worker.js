// CSV Parser Web Worker
// Runs CSV parsing on a separate thread to avoid blocking the main thread

importScripts('https://cdn.jsdelivr.net/npm/papaparse@5.4.1/papaparse.min.js');

self.onmessage = function(event) {
  const { fileData, tickerCol, sharesCol, costCol } = event.data;

  try {
    // Parse CSV in the worker
    const results = Papa.parse(fileData, {
      header: true,
      skipEmptyLines: true,
    });

    if (results.errors.length > 0) {
      self.postMessage({
        type: 'error',
        error: results.errors[0].message,
      });
      return;
    }

    const holdings = [];

    results.data.forEach((row, idx) => {
      try {
        if (!row[tickerCol] || !row[sharesCol] || !row[costCol]) {
          return;
        }

        const ticker = String(row[tickerCol]).trim().toUpperCase();
        const shares = parseFloat(String(row[sharesCol]).replace(/[^\d.]/g, '')) || 0;
        const cost = parseFloat(String(row[costCol]).replace(/[^\d.]/g, '')) || 0;

        if (ticker && shares > 0 && cost > 0) {
          holdings.push({
            id: `csv-${Date.now()}-${idx}`,
            ticker,
            shares,
            costBasis: cost,
          });
        }
      } catch (err) {
        console.warn(`Row ${idx + 2} parsing error:`, err.message);
      }
    });

    self.postMessage({
      type: 'success',
      holdings: holdings,
      count: holdings.length,
    });
  } catch (error) {
    self.postMessage({
      type: 'error',
      error: error.message,
    });
  }
};
