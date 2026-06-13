import { useState, useRef, useEffect } from 'react'
import './Tooltip.css'

export const GLOSSARY = {
  confidence:
    'How strongly the AI backs this signal, scored 1–10. A 7+ means several data points agree. Never a guarantee — treat it as a starting point, not a certainty.',
  buy:
    'The data supports adding this stock right now. Always do your own check before acting.',
  hold:
    'Keep it if you own it, but the data doesn\'t make a strong case for buying more right now.',
  avoid:
    'More red flags than green flags in the data right now. Not a permanent verdict — signals change as conditions do.',
  pe:
    'Price-to-Earnings ratio — how many dollars investors pay per $1 the company earns. A lower P/E can mean cheaper; a higher P/E often means the market expects fast growth.',
  dividend:
    'A cash payment the company sends to shareholders, usually each quarter. The yield is that payment as a percentage of the current stock price — like interest on your investment.',
  catalyst:
    'A specific upcoming event — an earnings report, product launch, or regulatory decision — that could move the stock price soon.',
  moat:
    'A lasting competitive advantage that protects the company from rivals: a strong brand, patents, or a network that\'s hard to copy.',
  invalidation:
    'The condition that would prove this signal wrong. If it happens, the original thesis no longer holds — a cue to reconsider.',
  accuracy:
    'How often this type of signal turned out to be correct in the past, based on real outcomes tracked over time.',
  return3m:
    'How much the stock price has moved over the last 3 months (13 weeks). Positive = risen; negative = fallen.',
  earnings:
    'The quarterly financial report where a company reveals profits, revenue, and forecasts. It often moves the stock price significantly.',
  range52:
    'Where the current price sits within the stock\'s highest and lowest price over the past year. 90% means it\'s near a 52-week high.',
  revenue:
    'How fast the company\'s annual sales have grown, averaged over 5 years. Growth here is the engine behind long-term stock gains.',
  margin:
    'Profit margin — of every dollar in sales, how many cents the company keeps after paying all its costs.',
  sector:
    'The industry the company operates in, like Technology, Healthcare, or Energy. Useful for spotting if your portfolio is too concentrated in one area.',
}

function Tooltip({ term, children }) {
  const [visible, setVisible] = useState(false)
  const ref = useRef(null)
  const definition = GLOSSARY[term]

  useEffect(() => {
    if (!visible) return
    const close = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setVisible(false)
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [visible])

  if (!definition) return children

  return (
    <span
      ref={ref}
      className="glossary-trigger"
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onClick={(e) => { e.stopPropagation(); setVisible(v => !v) }}
    >
      {children}
      {visible && (
        <span className="glossary-bubble" role="tooltip">
          {definition}
        </span>
      )}
    </span>
  )
}

export default Tooltip
