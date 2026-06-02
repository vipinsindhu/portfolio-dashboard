/**
 * Investment Recommendation Logic
 * Ported from generate_dashboard.py's generateRecommendation() function
 */

export function computeRecommendation(amount, timeline, existing, risk, healthScore) {
  // Determine macro regime
  let regime, regimeColor, regimeLabel;
  if (healthScore >= 70) {
    regime = 'bullish';
    regimeColor = '#34d399';
    regimeLabel = 'BULLISH';
  } else if (healthScore >= 55) {
    regime = 'constructive';
    regimeColor = '#60a5fa';
    regimeLabel = 'CONSTRUCTIVE';
  } else if (healthScore >= 45) {
    regime = 'neutral';
    regimeColor = '#9ca3af';
    regimeLabel = 'NEUTRAL';
  } else if (healthScore >= 30) {
    regime = 'cautious';
    regimeColor = '#fbbf24';
    regimeLabel = 'CAUTIOUS';
  } else {
    regime = 'bearish';
    regimeColor = '#f87171';
    regimeLabel = 'BEARISH';
  }

  // Build allocation based on regime + risk
  let equityAlloc = 60;
  let bondAlloc = 30;
  let cashAlloc = 10;

  const riskMap = { conservative: 'conservative', moderate: 'moderate', aggressive: 'aggressive' };
  const r = riskMap[risk] || 'moderate';

  if (regime === 'bearish') {
    equityAlloc = r === 'aggressive' ? 40 : r === 'moderate' ? 25 : 10;
    bondAlloc = r === 'aggressive' ? 40 : r === 'moderate' ? 50 : 60;
    cashAlloc = r === 'aggressive' ? 20 : 40;
  } else if (regime === 'cautious') {
    equityAlloc = r === 'aggressive' ? 65 : r === 'moderate' ? 50 : 30;
    bondAlloc = r === 'aggressive' ? 20 : r === 'moderate' ? 35 : 50;
    cashAlloc = r === 'aggressive' ? 15 : 35;
  } else if (regime === 'neutral') {
    equityAlloc = r === 'aggressive' ? 70 : r === 'moderate' ? 60 : 40;
    bondAlloc = r === 'aggressive' ? 20 : r === 'moderate' ? 30 : 45;
    cashAlloc = 10;
  } else if (regime === 'constructive') {
    equityAlloc = r === 'aggressive' ? 80 : r === 'moderate' ? 70 : 50;
    bondAlloc = r === 'aggressive' ? 15 : r === 'moderate' ? 25 : 40;
    cashAlloc = 5;
  } else {
    // bullish
    equityAlloc = r === 'aggressive' ? 90 : r === 'moderate' ? 80 : 60;
    bondAlloc = r === 'aggressive' ? 8 : r === 'moderate' ? 15 : 30;
    cashAlloc = r === 'aggressive' ? 2 : 5;
  }

  // Adjust for timeline
  if (timeline === 'short') {
    cashAlloc += 10;
    equityAlloc -= 5;
    bondAlloc -= 5;
  }

  // Fund recommendations based on regime
  let funds;
  if (regime === 'bearish' || regime === 'cautious') {
    funds = {
      defensive: ['XLV', 'XLP', 'XLU', 'VTV'],
      growth: ['VTI', 'QQQ', 'VWO'],
      bonds: ['BND', 'TLT', 'VGIT'],
      cash: ['SPAXX', 'GLD'],
    };
  } else if (regime === 'neutral') {
    funds = {
      value: ['VTV'],
      growth: ['QQQ'],
      international: ['VXUS'],
      bonds: ['BND', 'VGIT'],
      cash: ['SPAXX', 'GLD'],
    };
  } else {
    // constructive or bullish
    funds = {
      growth: ['QQQ', 'VUG', 'VB'],
      core: ['VTI', 'VWO', 'VXUS'],
      bonds: ['BND', 'VGIT'],
      cash: ['SPAXX'],
    };
  }

  return {
    healthScore,
    regime,
    regimeColor,
    regimeLabel,
    equityAlloc,
    bondAlloc,
    cashAlloc,
    funds,
    timeline,
    risk,
  };
}
