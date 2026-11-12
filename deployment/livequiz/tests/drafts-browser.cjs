// Against the isolated prepare-local.py fixture only.
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try {
  const page=await browser.newPage(),base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8765';
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'/_test_login.php');await page.goto(base+'/?new=1');
  await page.getByLabel('Quizens tittel').fill('Incomplete browser quiz');
  await page.getByRole('button',{name:'Lagre quiz',exact:true}).click();
  await page.getByText('Lagret på nett',{exact:true}).waitFor();
  const id=new URL(page.url()).searchParams.get('edit');
  await page.reload();
  await page.getByText('0 av 1 spørsmål er klare til spill.',{exact:false}).waitFor();
  await page.getByRole('button',{name:'Start spill',exact:true}).click();
  await page.getByText('Quizen har ingen ferdige spørsmål ennå.',{exact:false}).waitFor();
  assert.equal(new URL(page.url()).searchParams.get('edit'),id);
  await page.getByRole('button',{name:'Forhåndsvis hele quizen',exact:true}).click();
  await page.getByText('Fullfør minst ett spørsmål for å forhåndsvise spillet.',{exact:false}).waitFor();
  await page.getByRole('button',{name:'＋ Legg til spørsmål',exact:true}).click();
  let cards=page.locator('.question-editor');
  await cards.nth(1).getByLabel('Spørsmål',{exact:true}).fill('The only playable question');
  await cards.nth(1).getByLabel('Svartype').selectOption('text');
  await cards.nth(1).getByLabel('Godkjente svar – ett per linje').fill('Answer');
  await page.getByRole('button',{name:'＋ Legg til spørsmål',exact:true}).click();
  await cards.nth(2).getByLabel('Spørsmål',{exact:true}).fill('Still working on this');
  await cards.nth(2).getByLabel('Alternativ 1',{exact:true}).fill('Partial answer');
  await cards.nth(2).getByLabel('YouTube-lenke eller video-ID (valgfritt)').fill('https://youtu.be/partial');
  await page.getByRole('button',{name:'Lagre quiz',exact:true}).click();
  await page.getByText('Lagret på nett',{exact:true}).waitFor();await page.reload();
  await page.getByText('1 av 3 spørsmål er klare til spill.',{exact:false}).waitFor();
  assert.equal(await cards.count(),3);
  assert.equal(await cards.nth(2).getByLabel('Alternativ 1',{exact:true}).inputValue(),'Partial answer');
  assert.equal(await cards.nth(2).getByLabel('YouTube-lenke eller video-ID (valgfritt)').inputValue(),'https://youtu.be/partial');
  await page.getByRole('button',{name:'Forhåndsvis hele quizen',exact:true}).click();
  await page.getByRole('heading',{name:'Spørsmål 1 av 1',exact:true}).waitFor();
  await page.getByRole('button',{name:'Lukk forhåndsvisning',exact:true}).click();
  await page.getByRole('button',{name:'Start spill',exact:true}).click();
  await page.waitForURL('**/?host=*');
  const result=await page.evaluate(async id=>{
   const room=new URLSearchParams(location.search).get('host');
   return {state:await(await fetch('index.php?api=state&host=1&room='+room)).json(),quiz:await(await fetch('index.php?api=quiz&id='+id)).json()};
  },id);
  assert.equal(result.state.total,1);assert.equal(result.quiz.content.questions.length,3);
  await page.goto(base+'/?edit='+id);
  await cards.nth(0).getByLabel('Spørsmål',{exact:true}).fill('Now completed');
  await cards.nth(0).getByLabel('Svartype').selectOption('text');
  await cards.nth(0).getByLabel('Godkjente svar – ett per linje').fill('Done');
  await page.getByText('2 av 3 spørsmål er klare til spill.',{exact:false}).waitFor();
  await page.getByRole('button',{name:'Lagre quiz',exact:true}).click();await page.getByText('Lagret på nett',{exact:true}).waitFor();
  await page.getByRole('button',{name:'Start spill',exact:true}).click();await page.waitForURL('**/?host=*');
  const total=await page.evaluate(async()=>{const room=new URLSearchParams(location.search).get('host');return (await(await fetch('index.php?api=state&host=1&room='+room)).json()).total;});
  assert.equal(total,2);assert.deepEqual(errors,[]);
  console.log('Incomplete quiz browser passed: blank save/reload, all-draft guard, partial fields retained, preview/play filtering and later completion.');
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
