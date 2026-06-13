import { render, screen } from '@testing-library/react'
import SignalCard from '../components/shared/SignalCard'

const baseSignal = {
  ticker: 'AAPL',
  direction: 'buy',
  confidence: 8,
  rationale: 'Strong momentum and earnings growth',
  sector: 'Technology',
}

describe('SignalCard', () => {
  test('renders ticker symbol and sector', () => {
    render(<SignalCard signal={baseSignal} />)
    expect(screen.getByText('AAPL')).toBeInTheDocument()
    expect(screen.getByText('Technology')).toBeInTheDocument()
  })

  test('renders BUY badge for buy direction', () => {
    render(<SignalCard signal={baseSignal} />)
    expect(screen.getByText('BUY')).toBeInTheDocument()
  })

  test('renders HOLD badge for hold direction', () => {
    render(<SignalCard signal={{ ...baseSignal, direction: 'hold' }} />)
    expect(screen.getByText('HOLD')).toBeInTheDocument()
  })

  test('renders AVOID badge for avoid direction', () => {
    render(<SignalCard signal={{ ...baseSignal, direction: 'avoid' }} />)
    expect(screen.getByText('AVOID')).toBeInTheDocument()
  })

  test('renders rationale text', () => {
    render(<SignalCard signal={baseSignal} />)
    expect(screen.getByText('Strong momentum and earnings growth')).toBeInTheDocument()
  })

  test('renders 10 confidence bars with correct fill count', () => {
    const { container } = render(<SignalCard signal={baseSignal} />)
    const bars = container.querySelectorAll('.bar')
    const filled = container.querySelectorAll('.bar.filled')
    expect(bars).toHaveLength(10)
    expect(filled).toHaveLength(8)
  })

  test('shows P/E ratio when provided', () => {
    render(<SignalCard signal={{ ...baseSignal, pe_ratio: 25.4 }} />)
    expect(screen.getByText('P/E 25.4')).toBeInTheDocument()
  })

  test('shows dividend yield when > 0', () => {
    render(<SignalCard signal={{ ...baseSignal, dividend_yield: 0.025 }} />)
    expect(screen.getByText('2.5% dividend')).toBeInTheDocument()
  })

  test('hides cue badges when neither P/E nor dividend provided', () => {
    const { container } = render(<SignalCard signal={baseSignal} />)
    expect(container.querySelector('.signal-cues')).toBeNull()
  })

  test('shows portfolio weight when provided', () => {
    render(<SignalCard signal={baseSignal} weight={0.15} />)
    expect(screen.getByText('15.0%')).toBeInTheDocument()
  })

  test('hides portfolio weight when not provided', () => {
    const { container } = render(<SignalCard signal={baseSignal} />)
    expect(container.querySelector('.portfolio-weight')).toBeNull()
  })

  test('shows portfolio context when provided', () => {
    render(<SignalCard signal={{ ...baseSignal, portfolio_context: 'Overweight this position' }} />)
    expect(screen.getByText('Overweight this position')).toBeInTheDocument()
  })

  test('does not show portfolio context section when absent', () => {
    const { container } = render(<SignalCard signal={baseSignal} />)
    expect(container.querySelector('.portfolio-context')).toBeNull()
  })
})
