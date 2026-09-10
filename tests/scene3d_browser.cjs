/* node tests/scene3d_browser.cjs /tmp/demo/html (requires Playwright). */
const assert=require('node:assert/strict');
const path=require('node:path');
const fs=require('node:fs');
const http=require('node:http');
const {chromium}=require('playwright');
(async()=>{
    const root=path.resolve(process.argv[2]);
    const server=http.createServer((req,res)=>{
        const file=path.resolve(root,'.'+decodeURIComponent(req.url.split('?')[0]));
        if(!file.startsWith(root+path.sep)){res.writeHead(403).end();return;}
        fs.readFile(file,(err,data)=>{if(err){res.writeHead(404).end();return;}
            res.setHeader('Content-Type',({'.js':'text/javascript','.css':'text/css','.html':'text/html','.json':'application/json','.png':'image/png','.woff2':'font/woff2'})[path.extname(file)]||'application/octet-stream');res.end(data);});
    });
    await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));
    const base=`http://127.0.0.1:${server.address().port}`;
    const browser=await chromium.launch({headless:true,...(process.env.MUNCH_CHROMIUM?{executablePath:process.env.MUNCH_CHROMIUM}:{})});
    try {
        const page=await browser.newPage({viewport:{width:1100,height:900}}),errors=[];
        page.on('pageerror',e=>errors.push(e.message));
        await page.route('**/*',route=>route.request().url().startsWith(base)?route.continue():route.abort());
        await page.goto(base+'/index.html');
        const first=page.locator('.munch-3d').first();
        await first.scrollIntoViewIfNeeded();
        await page.waitForFunction(()=>document.querySelector('.munch-3d').classList.contains('munch-3d-ready'));
        assert.equal(await first.locator('canvas').count(),1);
        assert.deepEqual(await first.evaluate(el=>el.munch3d.errors),[]);
        const before=await first.evaluate(el=>el.munch3d.panel.getCamera());
        await first.getByRole('button',{name:'Rotate right',exact:true}).click();
        const rotated=await first.evaluate(el=>el.munch3d.panel.getCamera().azim);
        assert.notEqual(rotated,before.azim);
        await first.locator('input[type=range]').fill('4');
        assert.equal(await first.evaluate(el=>el.munch3d.vars.a),2);
        assert.equal(await first.evaluate(el=>el.munch3d.panel.getCamera().azim),rotated);
        assert.deepEqual(await first.evaluate(el=>el.munch3d.items.find(p=>p.type==='point').points[0]),[2,1,2]);
        assert.ok(await first.locator('.katex').count()>0);
        await first.getByRole('button',{name:'Reset view',exact:true}).click();
        assert.ok(Math.abs(await first.evaluate(el=>el.munch3d.panel.getCamera().azim)-before.azim)<1e-9);
        await first.locator('.munch-3d-board').scrollIntoViewIfNeeded();
        const box=await first.locator('.munch-3d-board').boundingBox();
        await page.mouse.move(box.x+box.width*.8,box.y+box.height*.3);await page.mouse.down();
        await page.mouse.move(box.x+box.width*.6,box.y+box.height*.5,{steps:10});await page.mouse.up();
        assert.notEqual(await first.evaluate(el=>el.munch3d.panel.getCamera().azim),before.azim);
        await page.screenshot({path:'/tmp/munch-scene3d-desktop.png'});
        await page.setViewportSize({width:390,height:844});await first.scrollIntoViewIfNeeded();
        await page.waitForFunction(()=>document.querySelector('.munch-3d-board').clientWidth<390);
        await page.screenshot({path:'/tmp/munch-scene3d-mobile.png'});
        // Touch rotation through the same canvas controls used on a mobile device.
        const cdp=await page.context().newCDPSession(page);
        await cdp.send('Emulation.setTouchEmulationEnabled',{enabled:true,maxTouchPoints:2});
        const touchBox=await first.locator('canvas').boundingBox(),az=await first.evaluate(el=>el.munch3d.panel.getCamera().azim);
        const point={x:touchBox.x+touchBox.width*.7,y:touchBox.y+touchBox.height*.4,id:1};
        await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[point]});
        await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{...point,x:point.x-50,y:point.y+30}]});
        await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
        assert.notEqual(await first.evaluate(el=>el.munch3d.panel.getCamera().azim),az);
        await page.emulateMedia({media:'print'});assert.equal(await first.locator('.munch-3d-fallback').isVisible(),true);await page.emulateMedia({media:'screen'});
        const second=page.locator('.munch-3d').nth(1);await second.scrollIntoViewIfNeeded();
        await page.waitForFunction(()=>document.querySelectorAll('.munch-3d')[1].classList.contains('munch-3d-ready'));
        assert.equal(await second.locator('input[type=range]').count(),0);
        assert.equal(await second.evaluate(el=>el.munch3d.gpu.panels.size),2);
        const third=page.locator('.munch-3d').nth(2);await third.scrollIntoViewIfNeeded();
        await page.waitForFunction(()=>document.querySelectorAll('.munch-3d')[2].classList.contains('munch-3d-ready'));
        assert.deepEqual(await third.evaluate(el=>el.munch3d.errors),[]);
        assert.equal(await third.evaluate(el=>el.munch3d.gpu.panels.size),3);
        const topology=await third.evaluate(el=>el.munch3d.items.filter(p=>p.type==='point').length);
        await third.locator('input[type=range]').fill('2');
        assert.ok(await third.evaluate(el=>el.munch3d.items.filter(p=>p.type==='point').length)>topology);
        assert.deepEqual(await third.evaluate(el=>el.munch3d.errors),[]);
        await third.locator('.munch-3d-board').scrollIntoViewIfNeeded();
        await page.screenshot({path:'/tmp/munch-scene3d-solids.png'});
        // Context recovery and removal release resources without accumulating GPU contexts.
        await page.evaluate(()=>{window.testGPU=document.querySelector('.munch-3d').munch3d.gpu;window.testLoss=window.testGPU.renderer.getContext().getExtension('WEBGL_lose_context');window.testLoss.loseContext();});
        await page.waitForFunction(()=>document.querySelector('.munch-3d').classList.contains('munch-3d-error'));
        await page.evaluate(()=>window.testLoss.restoreContext());
        await page.waitForFunction(()=>document.querySelectorAll('.munch-3d')[1].classList.contains('munch-3d-ready'));
        await page.evaluate(()=>document.querySelectorAll('.munch-3d').forEach(el=>el.remove()));
        await page.waitForFunction(()=>window.testGPU.panels.size===0&&window.testGPU.renderer===null);
        assert.deepEqual(errors.filter(e=>e!=="Identifier 'MultipleChoiceQuestion' has already been declared"),[]);
        const nojs=await browser.newPage({javaScriptEnabled:false});await nojs.goto(base+'/index.html');
        assert.equal(await nojs.locator('.munch-3d-fallback img').first().evaluate(img=>img.complete&&img.naturalWidth>0),true);
        const blocked=await browser.newPage();
        await blocked.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){return type.startsWith('webgl')?null:original.call(this,type,...args);};});
        await blocked.goto(base+'/index.html');await blocked.locator('.munch-3d').first().scrollIntoViewIfNeeded();
        await blocked.waitForFunction(()=>document.querySelector('.munch-3d').classList.contains('munch-3d-error'));
        assert.equal(await blocked.locator('.munch-3d-fallback').first().isVisible(),true);
        console.log('PASS: bundled assets, geometry, sliders, camera, mouse/touch, responsive layout, math labels, print, shared context, context recovery, disposal, no-JS/no-WebGL fallbacks');
    } finally {await browser.close();server.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
