/* NODE_PATH=/tmp/cw-browser-tests/node_modules node tests/calculator_browser.cjs /tmp/cw-integration/html */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { chromium } = require('playwright');
(async () => {
  const root = path.resolve(process.argv[2]);
  const server = http.createServer((req, res) => {
    const filename = path.resolve(root, '.' + decodeURIComponent(req.url.split('?')[0]));
    if (!filename.startsWith(root + path.sep)) { res.writeHead(403).end(); return; }
    fs.readFile(filename, (err, data) => {
      if (err) { res.writeHead(404).end(); return; }
      res.setHeader('Content-Type', ({ '.mjs': 'text/javascript', '.js': 'text/javascript', '.html': 'text/html', '.css': 'text/css' })[path.extname(filename)] || 'application/octet-stream'); res.end(data);
    });
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch({ headless: true, ...(process.env.MUNCH_CHROMIUM ? { executablePath: process.env.MUNCH_CHROMIUM } : {}) });
  try {
    const page = await browser.newPage({ viewport: { width: 1200, height: 1000 } });
    const errors = [], external = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.route('**/*', route => { if (route.request().url().startsWith(base)) return route.continue(); external.push(route.request().url()); return route.abort(); });
    await page.goto(base + '/index.html');
    assert.equal(await page.locator('iframe').count(), 0, 'calculator loads only on click');
    await page.locator('.cw-popup-button').first().click();
    const frame = page.frameLocator('.cw-popup-panel iframe').first();
    await frame.locator('[data-app="0"]').click();
    const key = k => frame.locator(`[data-key="${k}"]`).click();
    const text = () => frame.locator('.result').textContent();
    await key('frac'); await key('1'); await key('down'); await key('3'); await key('right'); await key('+'); await key('frac'); await key('1'); await key('down'); await key('6'); await key('EXE');
    assert.equal(await text(), '12');
    assert.equal(await frame.locator('.result .fraction').count(), 1);
    await key('FORMAT'); await frame.getByRole('button', { name: 'Decimal', exact: true }).click(); assert.equal(await text(), '0.5');
    await key('AC'); await key('root'); await key('8'); await key('EXE'); assert.equal(await text(), '2√2');
    await page.screenshot({ path: '/tmp/cw-desktop.png' });
    // Reopen keeps the same iframe and calculation.
    await page.getByRole('button', { name: 'Lukk kalkulator' }).click();
    await page.locator('.cw-popup-button').first().click(); assert.equal(await text(), '2√2');
    // Independent instances, no shared globals or shared storage keys.
    await page.getByRole('button', { name: 'Lukk kalkulator' }).click();
    await page.getByRole('button', { name: 'Second calculator' }).click();
    const second = page.frameLocator('.cw-popup-panel iframe').nth(1);
    await second.locator('[data-app="0"]').click(); assert.equal(await second.locator('.result').textContent(), '');
    await page.locator('.cw-popup-panel').nth(1).getByRole('button', { name: 'Lukk kalkulator' }).click();
    await page.locator('.cw-popup-button').first().click();
    // Drag using actual pointer events.
    const panel = page.locator('.cw-popup-panel').first(), bar = panel.locator('.cw-popup-bar');
    const before = await panel.boundingBox(), drag = await bar.boundingBox();
    await page.mouse.move(drag.x + 35, drag.y + 20); await page.mouse.down(); await page.mouse.move(drag.x + 110, drag.y + 50, { steps: 5 }); await page.mouse.up();
    const after = await panel.boundingBox(); assert.ok(after.x > before.x + 50);
    // Settings: radians; sin(pi/6) using physical keys.
    await key('SETTINGS'); await frame.getByRole('button', { name: 'Calc Settings' }).click(); await frame.getByRole('button', { name: 'Angle Unit' }).click(); await frame.getByRole('button', { name: 'Radian', exact: true }).click(); await key('AC');
    await key('AC'); await key('sin'); await key('SHIFT'); await key('7'); await key('/'); await key('6'); await key('EXE'); assert.equal(await text(), '12');
    // Real keyboard, error recovery and answer chaining.
    await key('AC'); await frame.locator('#lcd').focus(); await page.keyboard.type('1/0'); await page.keyboard.press('Enter'); assert.match(await frame.locator('#screen').textContent(), /Math ERROR/);
    await page.keyboard.press('Delete'); await page.keyboard.type('2+3*4'); await page.keyboard.press('Enter'); assert.equal(await text(), '14');
    await page.keyboard.type('+1'); await page.keyboard.press('Enter'); assert.equal(await text(), '15');
    // State persists across reload with a stable directive identity.
    await page.reload(); await page.locator('.cw-popup-button').first().click(); await frame.locator('[data-app="0"]').click(); assert.equal(await text(), '15');
    // Table setup and generation.
    await key('HOME'); await frame.locator('[data-app="2"]').click(); await frame.locator('[data-table="0"]').click();
    await key('x'); await key('square'); await key('EXE'); await frame.locator('[data-table="4"]').click();
    assert.match(await frame.locator('.table').textContent(), /25/);
    // One-variable statistics and correct sample deviation.
    await key('HOME'); await frame.locator('[data-app="1"]').click(); await frame.getByRole('button', { name: '1-Variable', exact: true }).click();
    for (const n of ['1', '2', '3']) { await key(n); await key('EXE'); }
    await key('TOOLS'); await frame.getByRole('button', { name: '1-Var Results', exact: true }).click();
    assert.match(await frame.locator('.result-list').textContent(), /x̄2/);
    // Math Box is functional, not a decorative menu.
    await key('HOME'); await frame.locator('[data-app="3"]').click(); await frame.locator('[data-box="3"]').click(); assert.equal(await frame.locator('.table tr').count(), 4);
    // Mobile fit: full keypad within frame, popup inside viewport.
    await page.setViewportSize({ width: 390, height: 844 });
    await key('HOME'); await page.screenshot({ path: '/tmp/cw-mobile.png' });
    const bounds = await panel.boundingBox(); assert.ok(bounds.x >= 0 && bounds.x + bounds.width <= 390);
    const physical = await frame.locator('#calculator').boundingBox(), exe = await frame.locator('[data-key="EXE"]').boundingBox();
    assert.ok(exe.y + exe.height <= physical.y + physical.height, 'EXE stays inside calculator body');
    // Resize a dialog: CSS scaling must keep every control accessible.
    await panel.evaluate(el => { el.style.width = '300px'; el.style.height = '500px'; });
    await frame.locator('#lcd').focus();
    await page.screenshot({ path: '/tmp/cw-small.png' });
    // Nested chapter resolves local module URLs, entirely offline.
    await page.goto(base + '/chapters/practice.html'); await page.locator('.cw-popup-button').click();
    await page.frameLocator('iframe').locator('[data-app="0"]').click();
    assert.deepEqual(errors, []); assert.deepEqual(external, []);
    console.log('Calculator browser checks passed; screenshots: /tmp/cw-desktop.png, /tmp/cw-mobile.png, /tmp/cw-small.png');
  } finally { await browser.close(); server.close(); }
})().catch(e => { console.error(e); process.exit(1); });
