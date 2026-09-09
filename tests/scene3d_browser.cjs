/* Run against the Sphinx demo emitted by test_scene3d.build_demo.
 * NODE_PATH=<directory containing playwright> node tests/scene3d_browser.cjs /tmp/demo/html
 */
const assert = require('node:assert/strict');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require('playwright');
(async()=>{
    const browser = await chromium.launch({headless:true,
        ...(process.env.MUNCH_CHROMIUM ? {executablePath:process.env.MUNCH_CHROMIUM} : {})});
    try {
        const page = await browser.newPage({viewport:{width:1100,height:900}});
        const errors=[];
        page.on('pageerror',err=>errors.push(err.message));
        await page.route(/^https?:/,route=>route.abort()); // Verify bundled renderer works offline.
        await page.goto(pathToFileURL(path.join(process.argv[2],'index.html')).href);
        const first=page.locator('.munch-3d').first();
        await first.scrollIntoViewIfNeeded();
        await page.waitForFunction(()=>document.querySelector('.munch-3d').classList.contains('munch-3d-ready'));
        assert.equal(await first.locator('.munch-3d-board svg').count(),1);
        assert.equal(await first.evaluate(el=>el.munch3d.entries.filter(x=>x.valid()).length),8);
        const before=await first.evaluate(el=>({az:el.munch3d.view.az_slide.Value(),el:el.munch3d.view.el_slide.Value()}));
        await first.getByRole('button',{name:'Rotate right',exact:true}).click();
        const rotated=await first.evaluate(el=>el.munch3d.view.az_slide.Value());
        assert.notEqual(rotated,before.az);
        await first.locator('input[type=range]').fill('4');
        assert.equal(await first.evaluate(el=>el.munch3d.vars.a),2);
        assert.equal(await first.evaluate(el=>el.munch3d.view.az_slide.Value()),rotated);
        const point=await first.evaluate(el=>{
            const p=el.munch3d.entries.find(x=>x.object.elType==='point3d').object;
            return [p.X(),p.Y(),p.Z()];
        });
        assert.deepEqual(point,[2,1,2]);
        assert.equal(await first.evaluate(el=>{
            const text=el.munch3d.entries.find(x=>x.object.elType==='text3d').object;
            return text.element2D.rendNode.textContent;
        }), 'P');
        await first.getByRole('button',{name:'Reset view',exact:true}).click();
        assert.equal(await first.evaluate(el=>el.munch3d.view.az_slide.Value()),before.az);
        const box=await first.locator('.munch-3d-board').boundingBox();
        await page.mouse.move(box.x+box.width*0.8,box.y+box.height*0.3);
        await page.mouse.down();await page.mouse.move(box.x+box.width*0.6,box.y+box.height*0.5,{steps:10});await page.mouse.up();
        assert.notEqual(await first.evaluate(el=>el.munch3d.view.az_slide.Value()),before.az);
        await page.screenshot({path:'/tmp/munch-scene3d-desktop.png'});
        await page.setViewportSize({width:390,height:844});
        await first.scrollIntoViewIfNeeded();
        await page.waitForFunction(()=>{
            const box=document.querySelector('.munch-3d-board');
            return box.clientWidth<390 && Math.abs(document.querySelector('.munch-3d').munch3d.board.canvasWidth-box.clientWidth)<2;
        });
        await page.screenshot({path:'/tmp/munch-scene3d-mobile.png'});
        await page.emulateMedia({media:'print'});
        assert.equal(await first.locator('.munch-3d-fallback').isVisible(),true);
        await page.emulateMedia({media:'screen'});
        const second=page.locator('.munch-3d').nth(1);
        await second.scrollIntoViewIfNeeded();
        await page.waitForFunction(()=>document.querySelectorAll('.munch-3d')[1].classList.contains('munch-3d-ready'));
        assert.equal(await second.locator('input[type=range]').count(),0);
        assert.equal(await second.evaluate(el=>el.munch3d.entries.length),1);
        // Existing global quiz assets declare this class twice on every book page.
        assert.deepEqual(errors.filter(e=>e!=="Identifier 'MultipleChoiceQuestion' has already been declared"),[]);
        const nojs=await browser.newPage({javaScriptEnabled:false});
        await nojs.goto(pathToFileURL(path.join(process.argv[2],'index.html')).href);
        assert.equal(await nojs.locator('.munch-3d-fallback img').first().evaluate(img=>img.complete && img.naturalWidth>0),true);
        console.log('PASS: offline renderer, primitives, sliders, camera, rotation, responsive layout, print, multiple boards, no-JS fallback');
    } finally {await browser.close();}
})().catch(err=>{console.error(err);process.exitCode=1;});
