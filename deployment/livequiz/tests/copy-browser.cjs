const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8798',owner=await browser.newPage(),guest=await browser.newPage({viewport:{width:390,height:844}});
 const errors=[];for(const p of [owner,guest])p.on('pageerror',e=>errors.push(e.message));
 await owner.goto(base+'/_test_login.php');
 const original=await owner.evaluate(async()=>{
  const boot=await(await fetch('index.php?api=bootstrap')).json(),headers={'X-CSRF-Token':boot.csrf};
  const post=async(action,data)=>(await(await fetch('index.php?api='+action,{method:'POST',headers:{...headers,'Content-Type':'application/json'},body:JSON.stringify(data)})).json());
  const canvas=document.createElement('canvas');canvas.width=100;canvas.height=100;canvas.getContext('2d').fillRect(0,0,100,100);
  const form=new FormData();form.append('image',await new Promise(r=>canvas.toBlob(r)),'copy.png');
  const image=(await(await fetch('index.php?api=upload',{method:'POST',headers,body:form})).json()).image;
  const quiz=await post('save',{content:{title:'Editable copy fixture',questions:[{type:'single',prompt:'Original question',code:'print(4)',youtube:'',image,seconds:30,options:['1','2','3','4'],correct:[3],accepted:[]}]}});
  return {...quiz,...await post('share',{id:quiz.id,enabled:true})};
 });
 await guest.goto(base+'/?public='+original.id);
 const anon=await guest.evaluate(async id=>{const boot=await(await fetch('index.php?api=bootstrap')).json();return(await fetch('index.php?api=copy',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify({id,source:'public'})})).status;},original.id);assert.equal(anon,401);
 await guest.getByRole('button',{name:'Logg inn for å lage en kopi',exact:true}).click();
 await guest.route('**/index.php?api=send',async route=>{await guest.request.get(base+'/_test_code.php?email='+encodeURIComponent(route.request().postDataJSON().email));await route.fulfill({json:{ok:true}});});
 await guest.getByLabel('E-post i Osloskolen').fill('copier@osloskolen.no');await guest.getByRole('button',{name:'Send kode',exact:true}).click();await guest.getByLabel('Engangskode').fill('12345678');await guest.getByRole('button',{name:'Logg inn',exact:true}).click();
 await guest.getByRole('button',{name:'Lag en redigerbar kopi',exact:true}).click();await guest.getByLabel('Quizens tittel').waitFor();
 const publicCopy=new URL(guest.url()).searchParams.get('edit');assert.notEqual(publicCopy,original.id);
 assert.equal(await guest.getByLabel('Quizens tittel').inputValue(),'Editable copy fixture (kopi)');
 await guest.getByRole('button',{name:'Forhåndsvis',exact:true}).click();
 await guest.waitForFunction(()=>[...document.querySelectorAll('img')].some(i=>i.naturalWidth===100));
 await guest.getByLabel('Spørsmål',{exact:true}).fill('My edited question');await guest.getByRole('button',{name:'Lagre quiz',exact:true}).click();await guest.getByText('Lagret · versjon 2',{exact:true}).waitFor();await guest.reload();assert.equal(await guest.getByLabel('Spørsmål',{exact:true}).inputValue(),'My edited question');
 await owner.goto(base+'/?edit='+original.id);assert.equal(await owner.getByLabel('Spørsmål',{exact:true}).inputValue(),'Original question');
 await guest.goto(base+'/?share='+original.id+'#key='+original.key);await guest.getByRole('button',{name:'Lag en redigerbar kopi',exact:true}).click();await guest.getByLabel('Quizens tittel').waitFor();const sharedCopy=new URL(guest.url()).searchParams.get('edit');assert.notEqual(sharedCopy,publicCopy);
 assert.equal(await guest.getByLabel('Spørsmål',{exact:true}).inputValue(),'Original question');
 const badCsrf=await guest.evaluate(async id=>(await fetch('index.php?api=copy',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,source:'public'})})).status,original.id);assert.equal(badCsrf,403);
 await guest.screenshot({path:'/tmp/livequiz-editable-copy.png'});assert.deepEqual(errors,[]);
 console.log('Copy browser checks passed: guest login return, public/shared copies, independent edits, image ownership, persistence and CSRF.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
