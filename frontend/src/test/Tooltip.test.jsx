import { render, screen, fireEvent } from '@testing-library/react'
import Tooltip, { GLOSSARY } from '../components/shared/Tooltip'

describe('Tooltip', () => {
  test('renders children', () => {
    render(<Tooltip term="confidence">Confidence</Tooltip>)
    expect(screen.getByText('Confidence')).toBeInTheDocument()
  })

  test('does not show bubble by default', () => {
    render(<Tooltip term="confidence">Confidence</Tooltip>)
    expect(screen.queryByRole('tooltip')).toBeNull()
  })

  test('shows bubble on mouse enter', () => {
    render(<Tooltip term="confidence">Confidence</Tooltip>)
    fireEvent.mouseEnter(screen.getByText('Confidence'))
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
    expect(screen.getByRole('tooltip').textContent).toBe(GLOSSARY.confidence)
  })

  test('hides bubble on mouse leave', () => {
    render(<Tooltip term="confidence">Confidence</Tooltip>)
    const trigger = screen.getByText('Confidence')
    fireEvent.mouseEnter(trigger)
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
    fireEvent.mouseLeave(trigger)
    expect(screen.queryByRole('tooltip')).toBeNull()
  })

  test('toggles bubble on click', () => {
    render(<Tooltip term="buy">BUY</Tooltip>)
    const trigger = screen.getByText('BUY')
    fireEvent.click(trigger)
    expect(screen.getByRole('tooltip')).toBeInTheDocument()
    fireEvent.click(trigger)
    expect(screen.queryByRole('tooltip')).toBeNull()
  })

  test('unknown term renders children with no tooltip wrapper behaviour', () => {
    const { container } = render(<Tooltip term="unknownxyz">raw text</Tooltip>)
    expect(screen.getByText('raw text')).toBeInTheDocument()
    expect(container.querySelector('.glossary-trigger')).toBeNull()
  })

  test('GLOSSARY has entries for all core terms', () => {
    const required = ['confidence', 'buy', 'hold', 'avoid', 'pe', 'dividend',
      'catalyst', 'moat', 'invalidation', 'accuracy']
    required.forEach(term => {
      expect(GLOSSARY[term]).toBeTruthy()
    })
  })

  test('glossary bubble contains the definition text', () => {
    render(<Tooltip term="moat">Edge</Tooltip>)
    fireEvent.mouseEnter(screen.getByText('Edge'))
    expect(screen.getByRole('tooltip').textContent).toBe(GLOSSARY.moat)
  })
})
