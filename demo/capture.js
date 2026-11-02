/**
 * Retake the screenshots in this folder from the running product.
 *
 * Needs Playwright (`npm i -g playwright`) and the stack running with demo data:
 *   API      http://localhost:8000    cd src/backend && python scripts/seed_dev.py   (creates demo@example.com)
 *   web      http://localhost:3000    cd src/web && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
 *   landing  http://localhost:3001    npm run build --workspace=src/landing && serve src/landing/out on 3001
 *
 * Usage:  NODE_PATH=$(npm root -g) node demo/capture.js        (writes next to this file)
 *         WEB=... LANDING=... node demo/capture.js ./some/dir
 */
const { chromium } = require('playwright');
const path = require('path');

const OUT = process.argv[2] || __dirname;
const WEB = process.env.WEB || 'http://localhost:3000';
const LANDING = process.env.LANDING || 'http://localhost:3001';
const HIDE_DEV_BADGE = 'nextjs-portal{display:none !important}';

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, deviceScaleFactor: 1 });
  ctx.setDefaultTimeout(10000);
  const file = (name) => path.join(OUT, name);

  // Landing page: first screen, and the trust section
  const lp = await ctx.newPage();
  await lp.goto(LANDING + '/');
  await lp.waitForLoadState('networkidle');
  await lp.screenshot({ path: file('landing.png'), clip: { x: 0, y: 0, width: 1280, height: 600 } });
  await lp.locator('#trust').screenshot({ path: file('landing-trust.png') });

  // Web app, signed in as the seeded demo user
  const p = await ctx.newPage();
  await p.goto(WEB + '/auth/login');
  await p.locator('#email').fill('demo@example.com');
  await p.locator('#password').fill('DemoPass!234');
  await Promise.all([p.waitForURL('**/dashboard'), p.getByRole('button', { name: /sign in/i }).click()]);
  await p.getByRole('heading', { name: 'Pending Drafts' }).waitFor();
  await p.addStyleTag({ content: HIDE_DEV_BADGE });
  await p.waitForTimeout(1200);

  // Pending drafts: the flagged draft plus one normal draft
  const section = p.getByRole('heading', { name: 'Pending Drafts' }).locator('xpath=ancestor::section[1]');
  const box = await section.boundingBox();
  const second = await p.locator('article').nth(1).boundingBox();
  await p.screenshot({
    path: file('dashboard-drafts.png'),
    fullPage: true,
    clip: { x: box.x, y: box.y, width: box.width, height: second.y + second.height - box.y + 24 },
  });

  // Briefings + VIP senders
  await p.locator('[data-testid="briefings-panel"]').locator('xpath=..').screenshot({ path: file('dashboard-controls.png') });

  // Phone width
  const phone = await ctx.newPage();
  await phone.setViewportSize({ width: 390, height: 844 });
  await phone.goto(WEB + '/dashboard');
  await phone.getByRole('heading', { name: 'Pending Drafts' }).waitFor();
  await phone.addStyleTag({ content: HIDE_DEV_BADGE });
  await phone.waitForTimeout(800);
  await phone.screenshot({ path: file('dashboard-phone.png'), clip: { x: 0, y: 0, width: 390, height: 844 } });

  await browser.close();
  console.log('Screenshots written to', OUT);
})();
