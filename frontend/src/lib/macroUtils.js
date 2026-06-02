/**
 * Macro analysis utilities
 * Port of Python logic from generate_dashboard.py
 */

export function computeHealth(signals) {
  const vals = Object.values(signals);
  const sigSum = vals.reduce((acc, m) => acc + m.signal, 0);
  const n = vals.length;
  const score = Math.round(((sigSum + n) / (2 * n)) * 100);

  let label, color;
  if (score >= 70) {
    label = 'Bullish';
    color = '#34d399';
  } else if (score >= 55) {
    label = 'Constructive';
    color = '#60a5fa';
  } else if (score >= 45) {
    label = 'Neutral';
    color = '#9ca3af';
  } else if (score >= 30) {
    label = 'Cautious';
    color = '#fbbf24';
  } else {
    label = 'Bearish';
    color = '#f87171';
  }

  const posCount = vals.filter(m => m.signal > 0).length;
  const negCount = vals.filter(m => m.signal < 0).length;
  const neutralCount = vals.filter(m => m.signal === 0).length;

  return { score, label, color, posCount, negCount, neutralCount };
}

export function getSignalBadgeClass(signal) {
  if (signal === 1) return 'sig-green';
  if (signal === -1) return 'sig-red';
  return 'sig-blue';
}

export function getSignalText(signal) {
  if (signal === 1) return '↑ Tailwind';
  if (signal === -1) return '↓ Headwind';
  return '→ Neutral';
}

export const REGIMES = [
  {
    label: 'Bullish',
    score: '70+',
    color: '#34d399',
    action: 'Add equity %, increase risk',
  },
  {
    label: 'Constructive',
    score: '55–69',
    color: '#60a5fa',
    action: 'Balanced portfolio, normal allocation',
  },
  {
    label: 'Neutral',
    score: '45–54',
    color: '#9ca3af',
    action: 'Hedge with bonds/gold, wait for clarity',
  },
  {
    label: 'Cautious',
    score: '30–44',
    color: '#fbbf24',
    action: 'Reduce risk, raise cash, go defensive',
  },
  {
    label: 'Bearish',
    score: '<30',
    color: '#f87171',
    action: 'Aggressive deleveraging, prepare for corrections',
  },
];
