/* NODE_PATH=/path/to/node_modules node tests/notebook_browser.cjs /tmp/notebook-site
 * Requires a real Chromium browser and access to the Pyodide CDN. No mocked kernel.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const os = require('node:os');
const path = require('node:path');
const { chromium } = require('playwright');

(async () => {
  const root = fs.realpathSync(process.argv[2]);
  const artifacts = fs.mkdtempSync(path.join(os.tmpdir(), 'munch-notebook-browser-'));
  const mime = { '.html': 'text/html', '.js': 'application/javascript', '.json': 'application/json',
    '.css': 'text/css', '.wasm': 'application/wasm', '.svg': 'image/svg+xml', '.png': 'image/png' };
  const server = http.createServer((req, res) => {
    const pathname = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    // Host below a nested prefix to exercise relative worker and asset URLs.
    if (!pathname.startsWith('/bok/notebook/')) { res.writeHead(404).end(); return; }
    let file = path.resolve(root, '.' + pathname.slice('/bok/notebook'.length));
    if (file !== root && !file.startsWith(root + path.sep)) { res.writeHead(403).end(); return; }
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html');
    fs.readFile(file, (error, data) => {
      if (error) { res.writeHead(404).end(); return; }
      res.writeHead(200, { 'Content-Type': mime[path.extname(file)] || 'application/octet-stream' });
      res.end(data);
    });
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  const base = `http://127.0.0.1:${server.address().port}/bok/notebook/`;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  page.setDefaultTimeout(180000);
  const errors = [];
  page.on('pageerror', error => { errors.push(String(error)); console.error(error.stack); });
  page.on('dialog', dialog => dialog.accept());
  async function editor() {
    await page.waitForFunction(() => document.getElementById('status').textContent.startsWith('Klar.'));
    const frame = page.frames().find(frame => frame.url().includes('/lite/lab/'));
    await frame.waitForFunction(() => window.jupyterapp?.shell.currentWidget?.content?.model?.cells);
    return frame;
  }
  async function model(frame) {
    return frame.evaluate(() => window.jupyterapp.shell.currentWidget.content.model.toJSON());
  }
  async function output(frame, expected) {
    await frame.waitForFunction(expected => JSON.stringify(
      window.jupyterapp.shell.currentWidget?.content?.model?.toJSON()
    ).includes(expected), expected, { timeout: 180000 });
  }
  try {
    await page.goto(base);
    assert.equal(await page.locator('.card').count(), 3);
    assert.ok(!page.frames().some(frame => frame.url().includes('/lite/')), 'landing page does not start Python');
    await page.screenshot({ path: path.join(artifacts, 'startside.png') });
    await page.locator('.card').first().click();
    let frame = await editor();
    assert.equal(await frame.locator('html').getAttribute('lang'), 'nb-NO');
    assert.equal(await frame.getByRole('menuitem', { name: 'Fil', exact: true }).count(), 1);
    let data = await model(frame);
    assert.ok(data.cells.filter(c => c.cell_type === 'code').every(c => c.execution_count === null));
    await page.locator('#run-all').click();
    await output(frame, 'Om fem år er du 21 år.');
    console.log('Python execution and persistent variables passed.');

    // Edit metadata and a cell, then download using the actual browser download flow.
    await frame.evaluate(() => {
      const panel = window.jupyterapp.shell.currentWidget;
      panel.content.model.sharedModel.setMetadata('munchboka_test', { preserved: true });
      panel.content.model.cells.get(4).sharedModel.setSource('pris = 375\nprint(pris)');
    });
    const downloaded = page.waitForEvent('download');
    await page.locator('#download').click();
    const download = await downloaded;
    const filename = path.join(artifacts, 'elevarbeid.ipynb');
    await download.saveAs(filename);
    const exported = JSON.parse(fs.readFileSync(filename));
    assert.deepEqual(exported.metadata.munchboka_test, { preserved: true });
    assert.match(exported.cells[4].source, /375/);
    assert.ok(exported.cells[2].outputs.length);
    // A normal desktop-Jupyter kernelspec, raw cell and Markdown attachment.
    exported.metadata.kernelspec = { name: 'python3', display_name: 'Python 3 (ipykernel)', language: 'python' };
    exported.cells[0].attachments = { 'test.txt': { 'text/plain': 'æøå' } };
    exported.cells.push({ cell_type: 'raw', id: 'raw-test', metadata: {}, source: 'Råtekst: æøå' });
    const premade = path.join(artifacts, 'premade.ipynb');
    fs.writeFileSync(premade, JSON.stringify(exported));
    await page.locator('#file').setInputFiles(premade);
    await frame.waitForFunction(() => window.jupyterapp.shell.currentWidget?.context?.path.startsWith('premade-'));
    await frame.evaluate(() => window.jupyterapp.shell.currentWidget.context.ready);
    assert.deepEqual((await model(frame)).metadata.munchboka_test, { preserved: true });
    assert.deepEqual((await model(frame)).cells[0].attachments, exported.cells[0].attachments);
    assert.equal((await model(frame)).cells.at(-1).source, 'Råtekst: æøå');
    await page.locator('#run-all').click();
    await output(frame, '375');
    console.log('Notebook download, upload and round-trip metadata passed.');

    // Autosave and reopening the browser-local workspace preserve edits.
    await frame.evaluate(() => window.jupyterapp.shell.currentWidget.context.save());
    await page.goto(base);
    await page.locator('#welcome-resume').click();
    frame = await editor();
    await frame.waitForFunction(() => window.jupyterapp.shell.currentWidget?.content?.model?.cells);
    assert.match((await model(frame)).cells[4].source, /375/);

    // A new original must not overwrite the existing student's exercise.
    await page.goto(base + '?notebook=01_python.ipynb');
    frame = await editor();
    await page.locator('#original').click();
    await frame.waitForFunction(() => window.jupyterapp.shell.currentWidget?.context?.path.includes('-ny-'));
    await frame.evaluate(() => window.jupyterapp.shell.currentWidget.context.ready);
    assert.equal((await model(frame)).cells[1].execution_count, null);

    // Data files in the notebook's directory are visible to browser Python.
    await frame.evaluate(async () => {
      const app = window.jupyterapp;
      const panel = app.shell.currentWidget;
      const directory = panel.context.path.slice(0, panel.context.path.lastIndexOf('/'));
      await app.serviceManager.contents.save(directory + '/data.csv', {
        type: 'file', format: 'text', content: 'x,y\n1,42\n'
      });
      panel.content.model.cells.get(1).sharedModel.setSource('print(open("data.csv").read())');
      panel.content.activeCellIndex = 1;
    });
    await page.locator('#run').click();
    await output(frame, '1,42');

    // Infinite Python must leave the shell responsive and recover through restart.
    await frame.evaluate(() => {
      const panel = window.jupyterapp.shell.currentWidget;
      panel.content.model.cells.get(1).sharedModel.setSource('while True:\n    pass');
      panel.content.activeCellIndex = 1;
    });
    await page.locator('#run').click();
    await frame.waitForFunction(() => window.jupyterapp.shell.currentWidget.sessionContext.kernelDisplayStatus === 'busy');
    await page.locator('#restart').click();
    await page.waitForFunction(() => document.getElementById('status').textContent.startsWith('Python er startet'));
    await frame.evaluate(() => {
      const panel = window.jupyterapp.shell.currentWidget;
      panel.content.model.cells.get(1).sharedModel.setSource('print("klar etter restart")');
      panel.content.activeCellIndex = 1;
    });
    await page.locator('#run').click();
    await output(frame, 'klar etter restart\\n');
    console.log('Infinite-loop recovery through kernel restart passed.');

    for (const name of ['02_funksjoner.ipynb', '03_sympy.ipynb']) {
      await page.goto(base + '?notebook=' + name);
      frame = await editor();
      await page.locator('#run-all').click();
      await frame.waitForFunction(() => {
        const cells = window.jupyterapp.shell.currentWidget.content.model.toJSON().cells.filter(c => c.cell_type === 'code');
        return cells.every(c => c.execution_count !== null) && window.jupyterapp.shell.currentWidget.sessionContext.kernelDisplayStatus === 'idle';
      });
      data = await model(frame);
      assert.ok(!data.cells.some(c => c.outputs?.some(o => o.output_type === 'error')), JSON.stringify(data));
      if (name.startsWith('02')) assert.ok(data.cells.some(c => c.outputs?.some(o => o.data?.['image/png'])));
      else assert.ok(data.cells.some(c => c.outputs?.some(o => o.data?.['text/latex'])));
      await page.screenshot({ path: path.join(artifacts, name + '.png') });
    }
    console.log('NumPy/Matplotlib plots and SymPy rich output passed.');

    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(artifacts, 'mobil.png') });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    assert.deepEqual(errors, []);
    console.log(`Notebook browser checks passed. Screenshots and exported notebook: ${artifacts}`);
  } finally {
    await browser.close();
    server.close();
  }
})().catch(error => { console.error(error); process.exit(1); });
