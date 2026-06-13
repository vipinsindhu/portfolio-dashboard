import { render, screen, fireEvent } from '@testing-library/react'
import FilterBar from '../components/tabs/ShortTerm/FilterBar'

const onFilterChange = vi.fn()

beforeEach(() => {
  onFilterChange.mockClear()
})

describe('FilterBar', () => {
  test('does not call fetch on mount', () => {
    const fetchSpy = vi.spyOn(global, 'fetch')
    render(<FilterBar onFilterChange={onFilterChange} />)
    expect(fetchSpy).not.toHaveBeenCalled()
    vi.restoreAllMocks()
  })

  test('renders filter toggle button', () => {
    render(<FilterBar onFilterChange={onFilterChange} />)
    expect(screen.getByText('Filters')).toBeInTheDocument()
  })

  test('controls are hidden until toggle is clicked', () => {
    render(<FilterBar onFilterChange={onFilterChange} />)
    expect(screen.queryByLabelText('Direction')).not.toBeInTheDocument()
    fireEvent.click(screen.getByText('Filters'))
    expect(screen.getByLabelText('Direction')).toBeInTheDocument()
  })

  test('shows sectors from prop when provided', () => {
    const sectors = ['Technology', 'Healthcare']
    render(<FilterBar onFilterChange={onFilterChange} sectors={sectors} />)
    fireEvent.click(screen.getByText('Filters'))
    expect(screen.getByRole('option', { name: 'Technology' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Healthcare' })).toBeInTheDocument()
  })

  test('always shows All Sectors option', () => {
    render(<FilterBar onFilterChange={onFilterChange} sectors={['Technology']} />)
    fireEvent.click(screen.getByText('Filters'))
    expect(screen.getByRole('option', { name: 'All Sectors' })).toBeInTheDocument()
  })

  test('uses fallback sectors when sectors prop is empty', () => {
    render(<FilterBar onFilterChange={onFilterChange} sectors={[]} />)
    fireEvent.click(screen.getByText('Filters'))
    expect(screen.getByRole('option', { name: 'Technology' })).toBeInTheDocument()
  })

  test('does not show clear button when no active filters', () => {
    render(<FilterBar onFilterChange={onFilterChange} />)
    expect(screen.queryByText('Clear')).not.toBeInTheDocument()
  })

  test('calls onFilterChange with direction when changed', () => {
    render(<FilterBar onFilterChange={onFilterChange} />)
    fireEvent.click(screen.getByText('Filters'))
    fireEvent.change(screen.getByLabelText('Direction'), { target: { value: 'buy' } })
    expect(onFilterChange).toHaveBeenCalledWith(
      expect.objectContaining({ direction: 'buy' })
    )
  })

  test('shows clear button and dot when filters are active', () => {
    render(<FilterBar onFilterChange={onFilterChange} />)
    fireEvent.click(screen.getByText('Filters'))
    fireEvent.change(screen.getByLabelText('Direction'), { target: { value: 'buy' } })
    expect(screen.getByText('Clear')).toBeInTheDocument()
    expect(document.querySelector('.filter-active-dot')).toBeInTheDocument()
  })

  test('resets all filters on clear click', () => {
    render(<FilterBar onFilterChange={onFilterChange} />)
    fireEvent.click(screen.getByText('Filters'))
    fireEvent.change(screen.getByLabelText('Direction'), { target: { value: 'buy' } })
    fireEvent.click(screen.getByText('Clear'))
    expect(onFilterChange).toHaveBeenLastCalledWith({ direction: 'all', min_confidence: 6, sector: null })
    expect(screen.queryByText('Clear')).not.toBeInTheDocument()
  })
})
