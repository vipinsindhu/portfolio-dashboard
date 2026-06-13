import { render, screen, fireEvent } from '@testing-library/react'
import SignalCardEnhanced from '../components/tabs/ShortTerm/SignalCardEnhanced'

const baseSignal = {
  ticker: 'META',
  direction: 'buy',
  confidence: 9,
  rationale: 'Strong ad revenue recovery and cost discipline.',
  sector: 'Technology',
  created_at: new Date(Date.now() - 60000).toISOString(), // 1 min ago
}

describe('SignalCardEnhanced', () => {
  test('renders ticker symbol', () => {
    render(<SignalCardEnhanced signal={baseSignal} />)
    expect(screen.getByText('META')).toBeInTheDocument()
  })

  test('renders sector', () => {
    render(<SignalCardEnhanced signal={baseSignal} />)
    expect(screen.getByText('Technology')).toBeInTheDocument()
  })

  test('renders BUY direction badge', () => {
    render(<SignalCardEnhanced signal={baseSignal} />)
    expect(screen.getByText('BUY')).toBeInTheDocument()
  })

  test('renders HOLD direction badge', () => {
    render(<SignalCardEnhanced signal={{ ...baseSignal, direction: 'hold' }} />)
    expect(screen.getByText('HOLD')).toBeInTheDocument()
  })

  test('renders AVOID direction badge', () => {
    render(<SignalCardEnhanced signal={{ ...baseSignal, direction: 'avoid' }} />)
    expect(screen.getByText('AVOID')).toBeInTheDocument()
  })

  test('renders 10 confidence bars with correct fill', () => {
    const { container } = render(<SignalCardEnhanced signal={baseSignal} />)
    expect(container.querySelectorAll('.bar')).toHaveLength(10)
    expect(container.querySelectorAll('.bar.filled')).toHaveLength(9)
  })

  test('rationale is collapsed by default', () => {
    const { container } = render(<SignalCardEnhanced signal={baseSignal} />)
    const p = container.querySelector('.rationale-text')
    expect(p.classList.contains('collapsed')).toBe(true)
  })

  test('Learn More expands rationale and changes label', () => {
    render(<SignalCardEnhanced signal={baseSignal} />)
    const btn = screen.getByRole('button', { name: /learn more/i })
    fireEvent.click(btn)
    expect(screen.getByRole('button', { name: /show less/i })).toBeInTheDocument()
  })

  test('shows 3-month return badge when provided', () => {
    const { container } = render(
      <SignalCardEnhanced signal={{ ...baseSignal, return_13w_pct: 12.5 }} />
    )
    const badge = container.querySelector('.cue-badge.positive')
    expect(badge).not.toBeNull()
    expect(badge.textContent).toContain('12.5%')
    expect(badge.textContent).toContain('3mo')
  })

  test('shows negative return badge for negative 3-month return', () => {
    const { container } = render(
      <SignalCardEnhanced signal={{ ...baseSignal, return_13w_pct: -8.3 }} />
    )
    const badge = container.querySelector('.cue-badge.negative')
    expect(badge).not.toBeNull()
    expect(badge.textContent).toContain('-8.3%')
  })

  test('shows earnings badge when days_until_earnings provided', () => {
    const { container } = render(
      <SignalCardEnhanced signal={{ ...baseSignal, days_until_earnings: 14 }} />
    )
    const badge = container.querySelector('.cue-badge.earnings')
    expect(badge).not.toBeNull()
    expect(badge.textContent).toContain('14d')
  })

  test('shows catalyst row when catalyst provided', () => {
    render(<SignalCardEnhanced signal={{ ...baseSignal, catalyst: 'Earnings beat expected' }} />)
    expect(screen.getByText('Earnings beat expected')).toBeInTheDocument()
  })

  test('shows invalidation row when invalidation provided', () => {
    render(<SignalCardEnhanced signal={{ ...baseSignal, invalidation: 'Revenue miss > 5%' }} />)
    expect(screen.getByText('Revenue miss > 5%')).toBeInTheDocument()
  })

  test('shows win rate badge when accuracy_pct provided', () => {
    render(<SignalCardEnhanced signal={{ ...baseSignal, accuracy_pct: 82 }} />)
    expect(screen.getByText(/82%/)).toBeInTheDocument()
  })

  test('does not show win rate badge when accuracy_pct is null', () => {
    const { container } = render(
      <SignalCardEnhanced signal={{ ...baseSignal, accuracy_pct: null }} />
    )
    expect(container.querySelector('.win-rate')).toBeNull()
  })

  test('shows time ago label when created_at provided', () => {
    render(<SignalCardEnhanced signal={baseSignal} />)
    expect(screen.getByText(/ago|just now/)).toBeInTheDocument()
  })
})
