/* node tests/asset_recovery_browser.cjs <Sphinx output> <relative page>
 * Use the fixture from test_asset_recovery.py. Requires Playwright; optional
 * MUNCH_CHROMIUM selects an installed Chrome executable.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');
const output = path.resolve(process.argv[2]);
const documentPath = process.argv[3] || 'chapter/exercises.html';
const assets = [
  'css/admonitions.css', 'css/part.css',
  'js/solution2.js', 'js/part.js', 'js/solution_timer.js',
];

(async () => {
  const browser = await chromium.launch({headless: true,
    ...(process.env.MUNCH_CHROMIUM ? {executablePath: process.env.MUNCH_CHROMIUM} : {})});
  try {
    for (const failures of [0, 1, 2, Infinity]) {
      const page = await browser.newPage();
      const counts = new Map();
      const errors = [];
      page.on('pageerror', error => { errors.push(error.message); console.error(error.message); });
      await page.route('**/*', async route => {
        const url = new URL(route.request().url());
        if (route.request().isNavigationRequest()) {
          return route.fulfill({body: fs.readFileSync(path.join(output, documentPath)), contentType: 'text/html'});
        }
        const asset = assets.find(asset => url.pathname.endsWith('/munchboka/' + asset));
        if (asset) {
          const count = (counts.get(asset) || 0) + 1;
          counts.set(asset, count);
          assert.equal(url.pathname, '/course/_static/munchboka/' + asset);
          assert(url.searchParams.has('v'));
          if (count > 1) assert.equal(url.searchParams.get('munchboka_retry'), String(count - 1));
          if (count <= failures) return route.abort('failed');
          return route.fulfill({
            body: fs.readFileSync(path.join(output, '_static/munchboka', asset)),
            contentType: asset.endsWith('.css') ? 'text/css' : 'text/javascript',
          });
        }
        // Keep unrelated widgets/CDNs outside this regression test.
        return route.fulfill({body: '', contentType: route.request().resourceType() === 'stylesheet' ? 'text/css' : 'text/javascript'});
      });
      await page.goto('https://recovery.test/course/' + documentPath);
      if (failures !== Infinity) {
        await page.waitForFunction(() =>
          document.querySelector('.answer-2-toggle').dataset.munchbokaToggleBound === 'true' &&
          document.querySelector('.solution-lock-status') &&
          getComputedStyle(document.querySelector('.part')).display === 'flex', null, {timeout: 5000}).catch(async error => {
            console.error('Requests per asset:', [...counts]);
            throw error;
          });
        // Check actual styling and interaction after late script recovery.
        assert.equal(await page.locator('.answer-2-toggle').evaluate(el => getComputedStyle(el).borderRadius), '999px');
        await page.locator('.answer-2-toggle').click();
        await page.waitForFunction(() => getComputedStyle(document.querySelector('.answer-2-content')).display !== 'none');
        assert.equal(await page.locator('.answer-2-toggle').getAttribute('aria-expanded'), 'true');
        await page.locator('.solution-2-toggle').first().click();
        assert.equal(await page.locator('.solution-2-toggle').first().getAttribute('aria-expanded'), 'true');
        await page.locator('.part-toggle').click();
        await page.waitForFunction(() => getComputedStyle(document.querySelector('.part-body')).display === 'none');
        await page.locator('.part-toggle').click();
        await page.waitForFunction(() => getComputedStyle(document.querySelector('.part-body')).display !== 'none');
        assert.deepEqual(errors, []);
      } else {
        await page.waitForTimeout(1800);
      }
      for (const asset of assets) assert.equal(counts.get(asset), Math.min(failures + 1, 3), asset);
      // CSS recovery must retain cascade order, including at nested URLs.
      const styles = await page.locator('link[rel="stylesheet"]').evaluateAll(nodes => nodes.map(node => node.href));
      assert(styles.findIndex(url => url.includes('/css/admonitions.css')) < styles.findIndex(url => url.includes('/css/part.css')));
      await page.close();
      console.log(`Asset recovery: ${failures} initial failures passed`);
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
