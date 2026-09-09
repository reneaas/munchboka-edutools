const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
(async()=>{
    const browser=await chromium.launch({headless:true,executablePath:process.env.MUNCH_CHROMIUM});
    try {
        const page=await browser.newPage({viewport:{width:1280,height:1000}}),errors=[];
        page.on('pageerror',e=>errors.push(e.message));
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
                    update.push(c.panels.map(p=>p.times.at(-1)));
                }
                const median=a=>a.sort((a,b)=>a-b)[Math.floor(a.length/2)];
                results.push({id:c.id,projectionErrorPx:Math.max(...errors),medianUpdateMs:[0,1].map(i=>median(update.slice(3).map(x=>x[i]))),buildMs:c.panels.map(p=>p.buildTimes[0])});
                c.camera({azim:-55,elev:25,zoom:1});
            }
            return results;
        });
        console.log(JSON.stringify({measurements,errors},null,2));
        fs.writeFileSync('/tmp/renderer3d-measurements.json',JSON.stringify(measurements,null,2));
        await page.locator('#labels').scrollIntoViewIfNeeded();
        await page.locator('#labels input[aria-label="a"]').fill('1.8');
        assert.equal(await page.evaluate(()=>comparison.cases.find(c=>c.id==='labels').vars.a),1.8);
        await page.setViewportSize({width:390,height:844});
        await page.locator('#sphere').scrollIntoViewIfNeeded();
        await page.waitForTimeout(200);
        await page.locator('#sphere').screenshot({path:'/tmp/renderer3d-mobile.png'});
        assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
        await page.evaluate(()=>document.body.style.zoom='1.5');
        await page.waitForTimeout(200);
        await page.locator('#labels').screenshot({path:'/tmp/renderer3d-label-zoom.png'});
        assert.equal(await page.locator('#labels .katex').count()>0,true);
        assert.equal(await page.evaluate(()=>comparison.gpu.contexts),1);
        assert.equal(await page.evaluate(()=>comparison.gpu.panels),8);
        await page.evaluate(()=>{for(const c of comparison.cases)c.dispose();});
        assert.equal(await page.evaluate(()=>comparison.gpu.panels),0);
        assert.deepEqual(errors,[]);
        console.log('PASS: eight pairs, camera sweep, sliders, narrow layout, math labels, CSS zoom, shared context, cleanup');
    } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
