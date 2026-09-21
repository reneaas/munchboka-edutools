/* NODE_PATH=/path/to/node_modules node tests/notebook_theme_browser.cjs /tmp/notebook-site */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { chromium } = require('playwright');

(async () => {
  const root = path.resolve(process.argv[2]);
  const artifacts = fs.mkdtempSync(path.join(os.tmpdir(), 'notebook-themes-'));
  const mime = { '.html': 'text/html', '.js': 'application/javascript', '.json': 'application/json',
    '.css': 'text/css', '.wasm': 'application/wasm', '.svg': 'image/svg+xml' };
  const server = http.createServer((req, res) => {
    const url = new URL(req.url, 'http://localhost');
    if (url.pathname === '/book.html') {
      res.writeHead(200, { 'Content-Type': 'text/html' });
      res.end('<!doctype html><html data-theme="light"><head><title>Book theme test</title></head>' +
        '<body style="margin:0"><iframe title="Notebook" src="/notebook/?notebook=01_python.ipynb" ' +
        'style="width:100%;height:900px;border:0"></iframe></body></html>');
      return;
    }
    if (!url.pathname.startsWith('/notebook/')) { res.writeHead(404).end(); return; }
    let file = path.resolve(root, '.' + decodeURIComponent(url.pathname.slice('/notebook'.length)));
    if (file !== root && !file.startsWith(root + path.sep)) { res.writeHead(403).end(); return; }
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
    fs.readFile(file, (error, data) => {
      if (error) { res.writeHead(404).end(); return; }
      res.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream' });
      res.end(data);
    });
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}`;
  const browser = await chromium.launch();
  const page = await browser.newPage({ colorScheme: 'dark', viewport: { width: 1280, height: 950 } });
  page.setDefaultTimeout(60000);
  const errors = [];
  page.on('pageerror', error => { errors.push(String(error)); console.error(error.stack); });
  page.on('console', message => { if (message.type() === 'error') console.error(message.text()); });
  page.on('dialog', dialog => dialog.accept());
  async function theme(shell, mode, withEditor = true) {
    console.log(`Checking ${mode} theme (${withEditor ? 'shell and editor' : 'landing'})`);
    await shell.waitForFunction(mode => document.documentElement.dataset.theme === mode, mode);
    assert.equal(await shell.evaluate(() => getComputedStyle(document.documentElement).colorScheme), mode);
    if (withEditor) {
      const editor = page.frames().find(f => f.url().includes('/lite/lab/'));
      await editor.waitForFunction(mode => document.body.dataset.jpThemeName ===
        (mode === 'dark' ? 'JupyterLab Dark' : 'JupyterLab Light'), mode);
      await shell.waitForFunction(() => document.getElementById('editor').classList.contains('theme-ready'));
    }
  }
  try {
    await page.goto(base + '/notebook/');
    await theme(page, 'dark', false);
    await page.screenshot({ path: path.join(artifacts, 'landing-dark.png') });
    await page.emulateMedia({ colorScheme: 'light' });
    await theme(page, 'light', false);
    await page.screenshot({ path: path.join(artifacts, 'landing-light.png') });
    await page.locator('.card').first().click();
    await page.waitForFunction(() => document.getElementById('status').textContent.startsWith('Klar.'));
    await theme(page, 'light');
    await page.emulateMedia({ colorScheme: 'dark' });
    await theme(page, 'dark');

    // Explicit book theme takes priority over the OS, even at startup.
    await page.goto(base + '/book.html');
    let shell = page.frames().find(f => f.url().includes('/notebook/?'));
    await shell.waitForFunction(() => document.getElementById('status').textContent.startsWith('Klar.'));
    await theme(shell, 'light');
    const editor = page.frames().find(f => f.url().includes('/lite/lab/'));
    await editor.waitForFunction(() => window.jupyterapp.shell.currentWidget.sessionContext.session?.kernel?.id);
    const original = await editor.evaluate(() => {
      window.themeTestMarker = Math.random();
      const panel = window.jupyterapp.shell.currentWidget;
      panel.content.model.cells.get(1).sharedModel.setSource('behold = 42');
      return { marker: window.themeTestMarker, path: panel.context.path, kernel: panel.sessionContext.session?.kernel?.id };
    });
    assert.ok(original.kernel, 'a live kernel must exist before testing theme changes');
    await page.evaluate(() => document.documentElement.dataset.theme = 'dark');
    await theme(shell, 'dark');
    await page.screenshot({ path: path.join(artifacts, 'embedded-dark.png') });
    await page.evaluate(() => document.documentElement.dataset.theme = 'light');
    await theme(shell, 'light');
    await page.screenshot({ path: path.join(artifacts, 'embedded-light.png') });

    // Legacy data-mode, automatic/system mode and rapid changes while CSS loads.
    await page.evaluate(() => {
      delete document.documentElement.dataset.theme;
      document.documentElement.dataset.mode = 'dark';
    });
    await theme(shell, 'dark');
    await page.evaluate(() => document.documentElement.dataset.mode = 'auto');
    await page.emulateMedia({ colorScheme: 'light' });
    await theme(shell, 'light');
    await page.evaluate(() => {
      document.documentElement.dataset.theme = 'dark';
      setTimeout(() => document.documentElement.dataset.theme = 'light', 10);
      setTimeout(() => document.documentElement.dataset.theme = 'dark', 20);
    });
    await theme(shell, 'dark');
    const after = await editor.evaluate(() => {
      const panel = window.jupyterapp.shell.currentWidget;
      return { marker: window.themeTestMarker, path: panel.context.path,
        kernel: panel.sessionContext.session?.kernel?.id, source: panel.content.model.cells.get(1).sharedModel.getSource() };
    });
    assert.equal(after.marker, original.marker, 'theme changes must not reload the editor');
    assert.equal(after.path, original.path);
    assert.equal(after.kernel, original.kernel, 'theme changes must not restart Python');
    assert.equal(after.source, 'behold = 42');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(artifacts, 'mobile-dark.png') });
    assert.ok(await shell.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    assert.deepEqual(errors, []);
    console.log(`Theme tests passed: OS, embedded theme, data-mode, auto, rapid changes, preserved editor/kernel. Screenshots: ${artifacts}`);
  } finally { await browser.close(); server.close(); }
})().catch(error => { console.error(error); process.exit(1); });
