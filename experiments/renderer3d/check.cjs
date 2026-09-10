const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
(async()=>{
    const browser=await chromium.launch({headless:true,executablePath:process.env.MUNCH_CHROMIUM});
    try {
        const page=await browser.newPage({viewport:{width:1280,height:1000},hasTouch:true}),errors=[];
        page.on('pageerror',e=>{errors.push(e.message);console.error(e.stack);});
        page.on('console',msg=>{if(msg.type()==='error')errors.push(msg.text());});
        await page.route('**/*',route=>new URL(route.request().url()).hostname==='127.0.0.1'?route.continue():route.abort());
        await page.goto('http://127.0.0.1:8766/experiments/renderer3d/');
        await page.waitForFunction(()=>window.comparison && document.querySelector('#health').textContent.startsWith('Ready'),{},{timeout:60000});
        assert.deepEqual(errors,[]);
        for(const id of ['sphere','planes','pyramid','surface','labels']) {
            const section=page.locator('#'+id);await section.scrollIntoViewIfNeeded();
            await section.screenshot({path:'/tmp/renderer3d-'+id+'.png'});
        }
        const measurements=await page.evaluate(async()=>{
            const results=[];
            for(const c of comparison.cases.slice(0,5)) {
                const [jsx,three]=c.panels;
                const errors=[[1,0,0],[0,1,0],[0,0,1]].map(p=>{const a=jsx.project(p),b=three.project(p);return Math.hypot(a[0]-b[0],a[1]-b[1]);});
                const update=[];
                for(let n=0;n<24;n++) {
                    c.camera({azim:-180+n*15,elev:25,zoom:1});
                    await new Promise(requestAnimationFrame);
                    update.push(c.panels.map(p=>p.lastUpdateMs));
                }
                const median=a=>a.sort((a,b)=>a-b)[Math.floor(a.length/2)];
                results.push({id:c.id,projectionErrorPx:Math.max(...errors),medianUpdateMs:[0,1].map(i=>median(update.slice(3).map(x=>x[i]))),buildMs:c.panels.map(p=>p.buildTimes[0])});
                c.camera({azim:-55,elev:25,zoom:1});
            }
            return results;
        });
        console.log(JSON.stringify({measurements,errors},null,2));
        assert.ok(measurements.every(m=>m.projectionErrorPx<1), 'matching camera projection');
        fs.writeFileSync('/tmp/renderer3d-measurements.json',JSON.stringify(measurements,null,2));
        for(const index of [0,1]) {
            const viewport=page.locator('#sphere .viewport').nth(index);
            await viewport.scrollIntoViewIfNeeded();
            const box=await viewport.boundingBox();
            const before=await page.evaluate(()=>comparison.cases[0].state.azim);
            await page.mouse.move(box.x+box.width*.75,box.y+box.height*.3);
            await page.mouse.down();await page.mouse.move(box.x+box.width*.5,box.y+box.height*.45,{steps:8});await page.mouse.up();
            await page.waitForFunction(value=>Math.abs(comparison.cases[0].state.azim-value)>1,before);
        }
        await page.locator('#labels').scrollIntoViewIfNeeded();
        await page.locator('#labels input[aria-label="a"]').fill('1.8');
        assert.equal(await page.evaluate(()=>comparison.cases.find(c=>c.id==='labels').vars.a),1.8);
        assert.deepEqual(errors,[], 'slider update');
        await page.setViewportSize({width:390,height:844});
        await page.locator('#sphere').scrollIntoViewIfNeeded();
        await page.waitForTimeout(200);
        await page.locator('#sphere').screenshot({path:'/tmp/renderer3d-mobile.png'});
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
        const cdp=await page.context().newCDPSession(page);
        const touch=[];
        for(const index of [0,1]) {
            const viewport=page.locator('#sphere .viewport').nth(index);
            await viewport.scrollIntoViewIfNeeded();const box=await viewport.boundingBox();
            const before=await page.evaluate(()=>comparison.cases[0].state.azim);
            const x=box.x+box.width*.75,y=box.y+box.height*.3;
            await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x,y}]});
            for(let i=1;i<=6;i++)await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x-i*8,y:y+i*3}]});
            await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});
            const after=await page.evaluate(()=>comparison.cases[0].state.azim);
            touch.push({renderer:index===0?'JSXGraph':'Three.js',rotated:Math.abs(after-before)>1,before,after});
        }
        console.log('Emulated touch observations',JSON.stringify(touch));
        fs.writeFileSync('/tmp/renderer3d-touch.json',JSON.stringify(touch,null,2));
        await page.evaluate(()=>document.body.style.zoom='1.5');
        await page.waitForTimeout(200);
        await page.locator('#labels').screenshot({path:'/tmp/renderer3d-label-zoom.png'});
        assert.equal(await page.locator('#labels .katex').count()>0,true);
        assert.equal(await page.evaluate(()=>comparison.gpu.contexts),1);
        assert.equal(await page.evaluate(()=>comparison.gpu.panels),8);
        assert.deepEqual(errors,[], 'resize and zoom');
        await page.evaluate(()=>{for(const c of comparison.cases)c.dispose();});
        assert.equal(await page.evaluate(()=>comparison.gpu.panels),0);
        assert.equal(await page.evaluate(()=>comparison.gpu.renderer.info.memory.geometries),0);
        assert.deepEqual(errors,[]);
        console.log('PASS: eight pairs, matched projection, camera sweep, mouse, sliders, narrow layout, math labels, CSS zoom, shared context, GPU geometry cleanup. Touch observations recorded separately.');
    } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
