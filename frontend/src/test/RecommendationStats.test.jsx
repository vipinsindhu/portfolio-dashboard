import { render, screen } from '@testing-library/react'
import RecommendationStats from '../components/tabs/ShortTerm/RecommendationStats'

const baseStats = {
  buy_count: 5,
  hold_count: 3,
  avoid_count: 2,
  avg_confidence: 7.4,
}

beforeEach(() => {
  vi.spyOn(global, 'fetch').mockResolvedValue({ ok: false })
})

afterEach(() => {
  vi.restoreAllMocks()
})

describe('RecommendationStats', () => {
  test('returns null when stats is null', () => {
    const { container } = render(<RecommendationStats stats={null} />)
    expect(container.firstChild).toBeNull()
  })

  test('shows buy/hold/avoid counts from stats', () => {
    render(<RecommendationStats stats={baseStats} />)
    expect(screen.getByText('5 Buy')).toBeInTheDocument()
    expect(screen.getByText('3 Hold')).toBeInTheDocument()
    expect(screen.getByText('2 Avoid')).toBeInTheDocument()
  })

  test('overrides counts from displayCounts when provided', () => {
    render(
      <RecommendationStats
        stats={baseStats}
        displayCounts={{ buy: 2, hold: 1, avoid: 1 }}
      />
    )
    expect(screen.getByText('2 Buy')).toBeInTheDocument()
    expect(screen.getByText('1 Hold')).toBeInTheDocument()
    expect(screen.getByText('1 Avoid')).toBeInTheDocument()
  })

  test('shows average confidence', () => {
    render(<RecommendationStats stats={baseStats} />)
    expect(screen.getByText('Avg 7.4/10')).toBeInTheDocument()
  })

  test('does not show win rate when accuracy fetch fails', () => {
    render(<RecommendationStats stats={baseStats} />)
    expect(screen.queryByText(/accuracy/)).not.toBeInTheDocument()
  })

  test('fetches accuracy data on mount', () => {
    render(<RecommendationStats stats={baseStats} />)
    expect(global.fetch).toHaveBeenCalledWith('/api/signals/accuracy')
  })
})
