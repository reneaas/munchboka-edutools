// Run with CHROMIUM_PATH=/path/to/chromium node --test tests/test_masonry_runtime.mjs
// Uses Chromium's debugging protocol directly; no npm dependencies are needed.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import {mkdtemp, readFile, rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import test from 'node:test';

const executable = process.env.CHROMIUM_PATH;
test('masonry packs, resizes, expands, preserves order and prints',
    {skip: !executable, timeout: 30000}, async t => {
    const profile = await mkdtemp(join(tmpdir(), 'masonry-browser-'));
    const browser = spawn(executable, ['--headless', '--no-sandbox', '--disable-gpu',
        '--disable-background-timer-throttling', '--disable-renderer-backgrounding',
        '--remote-debugging-port=0', `--user-data-dir=${profile}`, 'about:blank']);
    t.after(async () => {
        if (browser.exitCode === null && browser.signalCode === null) {
            const exited = new Promise(resolve => browser.once('exit', resolve));
            browser.kill('SIGKILL');
            await exited;
        }
        await rm(profile, {recursive: true, force: true});
    });
    const endpoint = await new Promise((resolve, reject) => {
        let output = '';
        browser.on('error', reject);
        browser.stderr.on('data', chunk => {
            output += chunk;
            const match = output.match(/DevTools listening on (ws:\/\/[^\s]+)/);
            if (match) resolve(match[1]);
        });
        browser.on('exit', code => reject(new Error(`Browser exited: ${code}\n${output}`)));
    });
    const socket = new WebSocket(endpoint);
    await new Promise(resolve => socket.addEventListener('open', resolve, {once: true}));
    t.after(() => socket.close());
    let serial = 0;
    const pending = new Map();
    socket.addEventListener('message', event => {
        const response = JSON.parse(event.data);
        const request = pending.get(response.id);
        if (!request) return;
        pending.delete(response.id);
        if (response.error) request.reject(new Error(JSON.stringify(response.error)));
        else request.resolve(response.result);
    });
    const send = (method, params = {}, sessionId) => new Promise((resolve, reject) => {
        const id = ++serial;
        pending.set(id, {resolve, reject});
        socket.send(JSON.stringify({id, method, params, sessionId}));
    });
    const {targetInfos} = await send('Target.getTargets');
    const {sessionId} = await send('Target.attachToTarget', {
        targetId: targetInfos.find(target => target.type === 'page').targetId, flatten: true,
    });
    const command = (method, params) => send(method, params, sessionId);
    const evaluate = async expression => {
        const result = await command('Runtime.evaluate', {expression, returnByValue: true,
            awaitPromise: true});
        assert.equal(result.exceptionDetails, undefined, JSON.stringify(result.exceptionDetails));
        return result.result.value;
    };
    await command('Page.enable');
    await command('Page.navigate', {url: 'data:text/html,<html><body></body></html>'});
    await command('Page.bringToFront');
    const settle = () => evaluate('new Promise(resolve => setTimeout(resolve, 100))');
    await settle();
    const css = await readFile(new URL('../src/munchboka_edutools/static/css/masonry.css', import.meta.url), 'utf8');
    const js = await readFile(new URL('../src/munchboka_edutools/static/js/masonry.js', import.meta.url), 'utf8');
    await evaluate(`document.body.innerHTML = ${JSON.stringify(`
        <style>${css}</style>
        <div class="mb-masonry" data-columns="1 2 3" data-placement="shortest"
             style="width:800px; --mb-masonry-gap:16px">
        ${[100, 300, 80, 120].map((height, i) => `<div class="mb-masonry-card" id="card${i}" style="height:${height}px">Card ${i}</div>`).join('')}
        </div>`)};
        window.grid = document.querySelector('.mb-masonry');
        window.cards = [...grid.children];`);
    // Progressive fallback before the controller runs.
    assert.equal(await evaluate("getComputedStyle(cards[0]).position"), 'static');
    await evaluate(js);
    await settle();
    const positions = () => evaluate(`cards.map(card => ({
        x: parseFloat(getComputedStyle(card).left),
        y: parseFloat(getComputedStyle(card).top),
        w: card.getBoundingClientRect().width
    }))`);
    assert.deepEqual(await positions(), [
        {x: 0, y: 0, w: 392}, {x: 408, y: 0, w: 392},
        {x: 0, y: 116, w: 392}, {x: 0, y: 212, w: 392},
    ]);
    assert.equal(await evaluate('grid.clientHeight'), 332);
    await evaluate("cards[0].style.height = '400px'");
    await settle();
    assert.equal((await positions())[2].x, 408);
    assert.equal((await positions())[2].y, 316);
    await evaluate("grid.dataset.placement = 'alternating'; grid.style.width = '801px'");
    await settle();
    assert.equal((await positions())[2].x, 0);
    assert.equal((await positions())[3].y, 316);
    await evaluate("grid.style.width = '450px'");
    await settle();
    assert.ok((await positions()).every(card => card.x === 0 && card.w === 450));
    assert.deepEqual(await evaluate('[...grid.children].map(card => card.id)'),
        ['card0', 'card1', 'card2', 'card3']);
    // Container queries use the container, not the viewport, and retry hidden grids.
    await evaluate("grid.style.display = 'none'; grid.style.width = '960px'");
    await settle();
    await evaluate("grid.style.display = ''");
    await settle();
    assert.ok(Math.abs((await positions())[0].w - (960 - 32) / 3) < 0.1);
    await command('Emulation.setEmulatedMedia', {media: 'print'});
    await settle();
    assert.equal(await evaluate('getComputedStyle(cards[0]).position'), 'static');
    assert.ok(await evaluate('grid.clientHeight >= 900'));
    await command('Emulation.setEmulatedMedia', {media: 'screen'});
    await settle();
    assert.equal(await evaluate('getComputedStyle(cards[0]).position'), 'absolute');
});
