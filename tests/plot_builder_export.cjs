// Browser regression: node tests/plot_builder_export.cjs <built page URL> <output.svg>
// Requires playwright; set CHROME_EXECUTABLE to use a system Chrome installation.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
const path = require('node:path');

(async () => {
    const browser = await chromium.launch({headless: true, executablePath: process.env.CHROME_EXECUTABLE});
    try {
        const page = await browser.newPage();
        const errors = [];
        page.on('pageerror', error => errors.push(error.message));
        await page.goto(process.argv[2]);
        await page.getByPlaceholder('f.eks. $x$', {exact: true}).fill(String.raw`$\vec{x}$`);
        await page.getByPlaceholder('f.eks. $y$', {exact: true}).fill(String.raw`$\alpha_1$`);
        await page.getByPlaceholder('navn (valgfritt)').fill(String.raw`$P_{\beta}$`);
        await page.getByText('+ Legg til tekst', {exact: true}).click();
        const textRow = page.getByPlaceholder('tekst', {exact: true}).locator('..');
        await textRow.getByPlaceholder('x', {exact: true}).fill('2');
        await textRow.getByPlaceholder('y', {exact: true}).fill('3');
        const fraction = String.raw`\frac{\sqrt{2}}{\pi}`;
        await page.getByPlaceholder('tekst', {exact: true}).fill(fraction);
        await page.waitForFunction(source => [...document.querySelectorAll('.JXGtext annotation')]
            .some(node => node.textContent === source), fraction);
        const liveLabels = await page.locator('.JXGtext annotation').allTextContents();
        const liveTicks = await page.locator('.plot-builder-board svg text').allTextContents();
        const downloadPromise = page.waitForEvent('download');
        await page.getByText('Last ned som SVG', {exact: true}).click();
        const download = await downloadPromise;
        const output = path.resolve(process.argv[3]);
        await download.saveAs(output);
        assert.deepEqual(errors, []);
        // Open the downloaded file with networking disabled: no page CSS/fonts.
        await page.context().setOffline(true);
        await page.goto(pathToFileURL(output).href);
        assert.equal(await page.locator('parsererror, foreignObject, .katex').count(), 0);
        const exported = await page.locator('svg[aria-label]').evaluateAll(nodes => nodes.map(node => ({
            source: node.getAttribute('aria-label'), paths: node.querySelectorAll('path').length,
            width: Number(node.getAttribute('width')), height: Number(node.getAttribute('height'))
        })));
        for (const source of liveLabels) {
            const label = exported.find(label => label.source === source);
            assert.ok(label, `Missing exported label: ${source}`);
            assert.ok(label.paths > 0 && label.width > 0 && label.height > 0, source);
        }
        assert.ok(exported.length >= 4);
        assert.ok(liveTicks.length > 0, 'Expected generated tick labels');
        assert.deepEqual(await page.locator('svg text').allTextContents(), liveTicks);
        assert.equal(await page.locator('[data-mml-node="merror"]').count(), 0);
        await page.screenshot({path: output + '.png'});
        console.log(`Verified ${exported.length} standalone math labels plus ${liveTicks.length} native tick labels.`);
    } finally {
        await browser.close();
    }
})().catch(error => { console.error(error); process.exitCode = 1; });
