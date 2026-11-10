// Run against a disposable prepare-local.py fixture seeded with an Algebra public lesson.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try {
  const owner=await browser.newContext(), anon=await browser.newContext();
  const page=await owner.newPage(), visitor=await anon.newPage();page.setDefaultTimeout(10000);visitor.setDefaultTimeout(10000);const errors=[];
  page.on('pageerror',e=>errors.push(e.message));visitor.on('pageerror',e=>errors.push(e.message));
  const base=process.env.TEST_URL||'http://127.0.0.1:8876';
  await visitor.goto(base+'/?search=1');await visitor.getByLabel('Søk etter tittel').fill('Algebra');await visitor.getByRole('button',{name:'Søk',exact:true}).click();
  await visitor.getByRole('link',{name:'Åpne spill',exact:true}).click();
  await visitor.getByRole('heading',{name:'Algebra public lesson',exact:true}).waitFor();
  assert.equal(await visitor.getByRole('button',{name:'Kopier til mine quizer'}).count(),0);
  await page.goto(base+'/_test_code.php');await page.locator('#code').fill('12345678');await page.getByRole('button',{name:'Logg inn',exact:true}).click();
  await page.goto(base+'/?search=1&q=Algebra');await page.getByRole('button',{name:'Kopier til mine quizer',exact:true}).click();
  await page.getByRole('heading',{name:'Rediger undervisningsquizen'}).waitFor();
  const copyId=new URL(page.url()).searchParams.get('edit');assert.ok(copyId);
  assert.equal(await page.getByLabel('Spillets tittel').inputValue(),'Algebra public lesson (kopi)');
  await page.getByLabel('Rad 2',{exact:true}).fill('300');await page.getByLabel('Rad 2',{exact:true}).press('Tab');
  await page.getByText('Lagret på nett',{exact:true}).waitFor();
  await page.reload();assert.equal(await page.getByLabel('Spørsmål',{exact:true}).first().inputValue(),'Question 500');
  await visitor.goto(base+'/?public='+copyId);await visitor.getByRole('heading',{name:'Algebra public lesson (kopi)',exact:true}).waitFor();
  await page.getByRole('switch').check();await page.getByText('Lagret på nett',{exact:true}).waitFor();
  const response=await visitor.reload();assert.equal(response.status(),404);await visitor.getByRole('alert').filter({hasText:'ikke offentlig'}).waitFor();
  await visitor.goto(base+'/?search=1&q=Algebra');assert.equal(await visitor.getByRole('link',{name:'Åpne spill',exact:true}).count(),1);
  const denied=await owner.request.post(base+'/',{form:{action:'copy',id:copyId,csrf:'invalid'}});assert.ok((await denied.text()).includes('Siden er utløpt'));
  await page.reload();assert.equal(await page.getByRole('switch').isChecked(),true);
  assert.deepEqual(errors,[]);console.log('Discovery browser passed: anonymous search/play, login/copy, row swap persisted, privacy removes public access/search, CSRF rejected.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
