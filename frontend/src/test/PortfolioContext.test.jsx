import { render, screen, act } from '@testing-library/react'
import { PortfolioProvider, usePortfolio } from '../context/PortfolioContext'

function TestConsumer() {
  const ctx = usePortfolio()
  return (
    <div>
      <span data-testid="has-portfolio">{String(ctx.hasPortfolio)}</span>
      <span data-testid="loading">{String(ctx.loading)}</span>
      <span data-testid="analysis">{ctx.analysis ? 'has-analysis' : 'no-analysis'}</span>
      <button onClick={() => ctx.updateHoldings([{ symbol: 'AAPL', quantity: 10, purchase_price: 150 }])}>
        Update
      </button>
      <button onClick={() => ctx.updateHoldings([])}>Clear</button>
      <button onClick={() => ctx.reload()}>Reload</button>
    </div>
  )
}

function renderWithProvider() {
  return render(
    <PortfolioProvider>
      <TestConsumer />
    </PortfolioProvider>
  )
}

describe('PortfolioContext', () => {
  beforeEach(() => {
    vi.spyOn(global, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => ({
        has_portfolio: true,
        analysis: { total_value: 1500 },
        long_term: null,
        short_term: null,
      }),
    })
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  test('starts with empty state on mount — no fetch called', () => {
    renderWithProvider()
    expect(screen.getByTestId('has-portfolio').textContent).toBe('false')
    expect(screen.getByTestId('loading').textContent).toBe('false')
    expect(screen.getByTestId('analysis').textContent).toBe('no-analysis')
    expect(global.fetch).not.toHaveBeenCalled()
  })

  test('updateHoldings sends POST to /api/portfolio/full', async () => {
    renderWithProvider()
    await act(async () => {
      screen.getByText('Update').click()
    })
    expect(global.fetch).toHaveBeenCalledWith('/api/portfolio/full', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ holdings: [{ symbol: 'AAPL', quantity: 10, purchase_price: 150 }] }),
    })
  })

  test('updateHoldings with empty array clears state without fetching', async () => {
    renderWithProvider()
    await act(async () => {
      screen.getByText('Clear').click()
    })
    expect(global.fetch).not.toHaveBeenCalled()
    expect(screen.getByTestId('has-portfolio').textContent).toBe('false')
    expect(screen.getByTestId('analysis').textContent).toBe('no-analysis')
  })

  test('sets hasPortfolio and analysis from API response', async () => {
    renderWithProvider()
    await act(async () => {
      screen.getByText('Update').click()
    })
    expect(screen.getByTestId('has-portfolio').textContent).toBe('true')
    expect(screen.getByTestId('analysis').textContent).toBe('has-analysis')
  })

  test('reload re-sends POST with current holdings', async () => {
    renderWithProvider()
    await act(async () => {
      screen.getByText('Update').click()
    })
    vi.clearAllMocks()
    await act(async () => {
      screen.getByText('Reload').click()
    })
    expect(global.fetch).toHaveBeenCalledTimes(1)
    expect(global.fetch).toHaveBeenCalledWith('/api/portfolio/full', expect.objectContaining({ method: 'POST' }))
  })

  test('non-ok response leaves hasPortfolio false', async () => {
    global.fetch.mockResolvedValueOnce({ ok: false })
    renderWithProvider()
    await act(async () => {
      screen.getByText('Update').click()
    })
    expect(screen.getByTestId('has-portfolio').textContent).toBe('false')
  })
})
