// Run only against the disposable prepare-local.py fixture.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
(async () => {
  const browser = await chromium.launch({headless:true, executablePath:process.env.CHROMIUM_PATH});
  try {
    const context = await browser.newContext(), page = await context.newPage();
    const base = process.env.LIVEQUIZ_BASE || 'http://127.0.0.1:8765';
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    await page.goto(base + '/_test_login.php');
    await page.goto(base + '/?new=1');
    await page.getByLabel('Quizens tittel').fill('Timeout recovery');
    await page.getByLabel('Spørsmål', {exact:true}).fill('Recovered question');
    await page.getByLabel('Svartype').selectOption('text');
    await page.getByLabel('Godkjente svar – ett per linje').fill('Answer');
    const save = () => page.getByRole('button', {name:'Lagre quiz',exact:true}).click();
    const saved = revision => page.getByText('Lagret på nett',{exact:true}).waitFor();
    // Commit the creation but lose its response: retry must return the same ID.
    let lost = false, attempts = [];
    await page.route('**/index.php?api=save', async route => {
      attempts.push(route.request().postDataJSON());
      const response = await route.fetch();
      if (!lost) { lost = true; await route.abort('failed'); }
      else await route.fulfill({response});
    });
    await save(); await saved(1);
    assert.ok(attempts.length >= 2); assert.deepEqual(attempts[0],attempts[1]);
    const id = new URL(page.url()).searchParams.get('edit');
    await page.unroute('**/index.php?api=save');
    // A stalled request releases the editor after its deadline and retries.
    let release, stalled = false;
    await page.route('**/index.php?api=save', async route => {
      if (!stalled) { stalled = true; await new Promise(resolve => release = resolve); }
      await route.continue();
    });
    await page.getByLabel('Quizens tittel').fill('Stalled save'); await save();
    await page.getByText('Lagring prøves igjen automatisk.',{exact:false}).waitFor();
    release(); await saved(2); await page.unroute('**/index.php?api=save');
    // A login in another tab rotates CSRF, but the original editor keeps saving.
    const login = await context.newPage(); await login.goto(base + '/_test_login.php');
    await page.getByLabel('Quizens tittel').fill('Fresh token'); await save(); await saved(3);
    // Expired authentication retains the draft and resumes after same-account login.
    await context.clearCookies();
    await page.getByLabel('Quizens tittel').fill('Expired session draft'); await save();
    await page.getByRole('link',{name:'Logg inn i en ny fane'}).waitFor();
    assert.ok(await page.evaluate(()=>Object.values(localStorage).some(v=>v.includes('Expired session draft'))));
    await login.goto(base + '/_test_login.php'); await save(); await saved(4);
    // Capture edits made while a successful request is in flight.
    release = null; let held = false;
    await page.route('**/index.php?api=save', async route => {
      const response = await route.fetch();
      if (!held) { held = true; await new Promise(resolve => release = resolve); }
      await route.fulfill({response});
    });
    await page.getByLabel('Quizens tittel').fill('First snapshot');
    const click = save();
    while (!release) await new Promise(resolve=>setTimeout(resolve,20));
    await page.getByLabel('Quizens tittel').fill('Later snapshot');
    release(); await click; await saved(6); await page.unroute('**/index.php?api=save');
    // Local recovery works even for incomplete content the server cannot accept.
    await page.getByLabel('Spørsmål',{exact:true}).fill('');
    page.once('dialog', dialog=>dialog.accept()); await page.reload();
    await page.getByRole('button',{name:'Gjenopprett utkast',exact:true}).click();
    assert.equal(await page.getByLabel('Spørsmål',{exact:true}).inputValue(),'');
    await page.getByLabel('Spørsmål',{exact:true}).fill('Recovered after reload'); await save(); await saved(7);
    assert.equal(await page.evaluate(()=>Object.keys(localStorage).filter(k=>k.startsWith('livequiz-draft:')).length),0);
    // The HTTP endpoint also rejects account-switch races, independently of JS.
    const denied = await page.evaluate(async id => {
      const session = await (await fetch('index.php?api=bootstrap')).json();
      return (await fetch('index.php?api=save',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':session.csrf,'X-Editor-Owner':'999'},body:JSON.stringify({id})})).status;
    },id);
    assert.equal(denied,403);
    // An actual newer revision is not overwritten by a stale editor.
    await page.evaluate(async id => {
      const session=await(await fetch('index.php?api=bootstrap')).json();
      const quiz=await(await fetch('index.php?api=quiz&id='+id)).json();
      quiz.content.title='Changed elsewhere';
      const r=await fetch('index.php?api=save',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':session.csrf},body:JSON.stringify(quiz)});
      if(!r.ok)throw new Error('Concurrent save failed');
    },id);
    await page.getByLabel('Quizens tittel').fill('Keep conflicting draft'); await save();
    await page.getByText('Quizen er endret i en annen fane.',{exact:false}).waitFor();
    assert.ok(await page.evaluate(()=>Object.values(localStorage).some(v=>v.includes('Keep conflicting draft'))));
    assert.deepEqual(errors,[]);
    console.log('Quiz editor recovery passed: lost response, timeout, token renewal, login expiry, edits during save, reload recovery, account guard and revision conflict.');
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
