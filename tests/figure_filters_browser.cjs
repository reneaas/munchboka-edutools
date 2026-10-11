/* node tests/figure_filters_browser.cjs
 * Requires Playwright. CHROME_EXECUTABLE can select an installed Chromium.
 * Regression: Safari 27.0.1 mispaints figures when a container brightness
 * filter is nested around the image/SVG's dark-mode inversion filter.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require('playwright');
const root = path.join(__dirname, '../src/munchboka_edutools/static/css');
const css = [
  'clickable_figures/style.css', 'misc_styles/figures.css',
  'general_style.css', 'figures.css',
].map(file => fs.readFileSync(path.join(root, file), 'utf8')).join('\n');
const drawing = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 60">' +
  '<path d="M10 50 L90 10" stroke="black" stroke-width="3"/></svg>';
const html = `<!doctype html><html data-mode="light"><style>${css}</style>
  <body style="width:600px">
  <figure><a class="adaptive-figure"><img id="external" class="adaptive-figure"
    style="width:60%" src="data:image/svg+xml;base64,${Buffer.from(drawing).toString('base64')}"></a></figure>
  <figure class="adaptive-figure plot-figure"><svg id="inline" class="graph-inline-svg"
    viewBox="0 0 100 60" style="width:60%"><path d="M10 50 L90 10"
    stroke="black" stroke-width="3"/></svg><figcaption>Caption</figcaption></figure>
  <img id="standalone" class="adaptive-figure" style="width:200px"
    src="data:image/svg+xml;base64,${Buffer.from(drawing).toString('base64')}">
  </body></html>`;

(async () => {
  const browser = await chromium.launch({headless: true,
    ...(process.env.CHROME_EXECUTABLE ? {executablePath: process.env.CHROME_EXECUTABLE} : {})});
  try {
    const page = await browser.newPage();
    await page.setContent(html);
    await page.evaluate(() => Promise.all([...document.images].map(img => img.decode())));
    let originalSizes;
    for (const [mode, system, inverted] of [
      ['light', 'dark', false], ['dark', 'light', true],
      ['auto', 'dark', true], ['auto', 'light', false], ['dark', 'dark', true],
    ]) {
      await page.emulateMedia({colorScheme: system});
      await page.evaluate(mode => { document.documentElement.dataset.mode = mode; }, mode);
      // Wait for the existing theme transition to finish before inspecting styles.
      await page.waitForFunction(inverted => {
        const filter = getComputedStyle(document.getElementById('inline')).filter;
        return filter === (inverted ? 'invert(1) hue-rotate(180deg)' : 'invert(0)');
      }, inverted);
      const figures = await page.locator('#external, #inline, #standalone').evaluateAll(elements =>
        elements.map(element => {
          const ancestors = [];
          for (let p = element.parentElement; p; p = p.parentElement) {
            ancestors.push({tag: p.tagName, filter: getComputedStyle(p).filter});
          }
          const {width, height} = element.getBoundingClientRect();
          return {id: element.id, filter: getComputedStyle(element).filter, ancestors, width, height};
        }));
      for (const figure of figures) {
        assert.equal(figure.filter, inverted ? 'invert(1) hue-rotate(180deg)' : 'invert(0)', figure.id);
        assert(figure.width > 0 && figure.height > 0, `${figure.id} must retain its layout`);
        for (const ancestor of figure.ancestors) {
          assert.equal(ancestor.filter, 'none',
            `${mode}/${system}: ${figure.id} must not have an additional filter on ${ancestor.tag}`);
        }
      }
      const sizes = figures.map(({width, height}) => ({width, height}));
      if (!originalSizes) originalSizes = sizes;
      else assert.deepEqual(sizes, originalSizes, 'theme changes must not resize figures');
      console.log(`PASS ${mode} / system ${system}`);
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
