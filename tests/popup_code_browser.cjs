/* UI integration check (Python execution is outside this test's scope).
 * Requires Playwright and the CDN versions used by the extension, downloaded as:
 * popup-code-jquery.js, popup-code-jquery-ui.js, popup-code-jquery-ui.css,
 * popup-code-codemirror.js, popup-code-codemirror.css in the supplied directory.
 * NODE_PATH=<playwright node_modules> node tests/popup_code_browser.cjs <vendor directory>
 * Optional MUNCH_CHROMIUM points to an existing Chrome executable.
 */
const assert = require('node:assert/strict');
const {chromium} = require('playwright');
const path = require('node:path');
const root = path.resolve(__dirname, '../src/munchboka_edutools/static') + '/';
const vendor = path.resolve(process.argv[2] || '/tmp');
(async () => {
 const browser = await chromium.launch({headless:true, ...(process.env.MUNCH_CHROMIUM ? {executablePath:process.env.MUNCH_CHROMIUM} : {})});
 try {
 const page = await browser.newPage({viewport:{width:1200,height:900}});
 const errors=[]; page.on('pageerror', e=>errors.push(e.message));
 await page.route('http://popup.test/**', r=>r.fulfill({body:'<!doctype html><html data-mode="light"><body></body></html>',contentType:'text/html'}));
 await page.goto('http://popup.test/');
 for(const path of [vendor + '/popup-code-jquery-ui.css',vendor + '/popup-code-codemirror.css',root+'css/cas_popup.css',root+'css/interactive_code.css',root+'css/popup_code.css']) await page.addStyleTag({path});
 for(const path of [vendor + '/popup-code-jquery.js',vendor + '/popup-code-jquery-ui.js',vendor + '/popup-code-codemirror.js',root+'js/interactiveCode/codeEditor.js',root+'js/interactiveCode/interactiveCodeSetup.js']) await page.addScriptTag({path});
 // Scope this check to window/editor UI: no downloads for optional addons or Python runtime.
 await page.evaluate(()=>{
 CodeEditor.prototype.loadAddons = async () => {};
 window.PythonRunner = class { constructor() {} };
 for(let i=0;i<2;i++) {
 const button=document.createElement('button'); button.textContent='Open '+i;
 button.setAttribute('aria-controls','popup-'+i);
 button.dataset.popupCode=JSON.stringify({width:700,height:550,title:'Python '+i,code:'print("</textarea> &amp; \\n ${x}")',predict:i===1});
 const content=document.createElement('div'); content.id='popup-'+i; content.className='popup-code-content'; content.style.display='none';
 const editor=document.createElement('div');editor.id='editor-'+i;content.append(editor);
 document.body.append(button,content);
 }
 });
 await page.addScriptTag({path:root+'js/popup_code.js'});
 assert.equal(await page.locator('.CodeMirror').count(),0);
 await page.getByText('Open 0',{exact:true}).click();
 await page.waitForSelector('.CodeMirror');
 await page.waitForTimeout(150);
 assert.equal(await page.locator('.CodeMirror').evaluate(e=>e.CodeMirror.getValue()),'print("</textarea> &amp; \\n ${x}")');
 await page.locator('.CodeMirror').evaluate(e=>e.CodeMirror.setValue('print(42)'));
 await page.locator('.pythonoutput').evaluate(e=>e.textContent='42');
 const panel=page.locator('.popup-code-window').first();
 const before=await panel.boundingBox(); const bar=await panel.locator('.ui-dialog-titlebar').boundingBox();
 await page.mouse.move(bar.x+60,bar.y+20);await page.mouse.down();await page.mouse.move(bar.x+150,bar.y+60,{steps:5});await page.mouse.up();
 const after=await panel.boundingBox();assert.ok(after.x>before.x+50);
 const handle=await panel.locator('.ui-resizable-se').boundingBox();
 await page.mouse.move(handle.x+5,handle.y+5);await page.mouse.down();await page.mouse.move(handle.x+70,handle.y+45,{steps:5});await page.mouse.up();
 assert.ok((await panel.boundingBox()).width>after.width+30);
 const placed=await panel.boundingBox();
 await panel.getByRole('button',{name:'Lukk',exact:true}).click();
 await page.getByText('Open 0',{exact:true}).click();
 assert.equal(await page.locator('.CodeMirror').count(),1);
 assert.equal(await page.locator('.CodeMirror').evaluate(e=>e.CodeMirror.getValue()),'print(42)');
 assert.equal(await page.locator('.pythonoutput').textContent(),'42');
 assert.ok(Math.abs((await panel.boundingBox()).x-placed.x)<2);
 await page.getByText('Open 1',{exact:true}).click();await page.waitForTimeout(150);
 assert.equal(await page.locator('.CodeMirror').count(),2);
 assert.equal(await page.locator('#editor-1 .CodeMirror').evaluate(e=>e.CodeMirror.getOption('readOnly')),true);
 await page.setViewportSize({width:375,height:667});
 await page.waitForTimeout(100);
 for(const p of await page.locator('.popup-code-window').all()) {const r=await p.boundingBox();assert.ok(r.x>=0 && r.x+r.width<=376);}
 await page.keyboard.press('Escape');
 assert.equal(await page.locator('[data-popup-code]').nth(1).getAttribute('aria-expanded'),'false');
 assert.deepEqual(errors,[]);

 console.log('PASS: lazy editor, literal code, drag, resize, retained state/position, independent prediction editor, viewport fit, Escape');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1)});
