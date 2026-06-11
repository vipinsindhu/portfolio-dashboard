/**
 * End-to-end smoke test.
 * Runs against a live instance of the app (Flask serving frontend/dist).
 * Usage: SMOKE_URL=http://localhost:5000 node smoke.js
 */
const { chromium } = require('playwright')

const BASE = process.env.SMOKE_URL || 'http://localhost:5000'

async function main() {
  const browser = await chromium.launch({ headless: true })
  let failures = 0

  const check = (name, ok) => {
    console.log(`${ok ? 'PASS' : 'FAIL'}: ${name}`)
    if (!ok) failures++
  }

  // Scenario 1: app loads, all five tabs render (desktop)
  const desktop = await browser.newContext({ viewport: { width: 1280, height: 800 } })
  const page = await desktop.newPage()
  await page.goto(BASE, { waitUntil: 'networkidle', timeout: 60000 })
  check('home page has app title', await page.getByText('Smart Stock Ideas').first().isVisible())
  const tabCount = await page.locator('.tab-button').count()
  check(`all 5 tabs render (found ${tabCount})`, tabCount === 5)

  // Scenario 2: demo flow — sample portfolio loads and analysis renders
  await page.getByRole('button', { name: /Try a Demo/i }).first().click()
  await page.waitForSelector('.portfolio-table-container', { timeout: 30000 })
  check('sample portfolio table renders', true)
  const health = page.getByText(/portfolio health/i).first()
  await health.waitFor({ timeout: 60000 })
  check('analysis results render', await health.isVisible())

  // Scenario 3: mobile viewport shows bottom-nav tabs
  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 } })
  const mPage = await mobile.newPage()
  await mPage.goto(BASE, { waitUntil: 'networkidle', timeout: 60000 })
  const mobileTabs = await mPage.locator('.tab-button:visible').count()
  check(`mobile shows 5 tabs (found ${mobileTabs})`, mobileTabs === 5)
  const barPosition = await mPage.locator('.tab-bar').evaluate(el => getComputedStyle(el).position)
  check(`mobile tab bar is fixed bottom nav (position: ${barPosition})`, barPosition === 'fixed')

  await browser.close()

  if (failures > 0) {
    console.error(`\n${failures} smoke check(s) failed`)
    process.exit(1)
  }
  console.log('\nAll smoke checks passed')
}

main().catch(err => { console.error(err); process.exit(1) })
