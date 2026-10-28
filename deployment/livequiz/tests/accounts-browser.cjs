/* Disposable prepare-local.py fixture only. Email delivery is stubbed; verification is real. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8795';
 const a=await browser.newPage({viewport:{width:390,height:844}}),b=await browser.newPage();
 const errors=[];for(const p of [a,b])p.on('pageerror',e=>errors.push(e.message));
 const api=(p,action,data,csrf=true)=>p.evaluate(async({action,data,csrf})=>{
  const boot=await(await fetch('index.php?api=bootstrap')).json();
  const r=await fetch('index.php?api='+action,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf?boot.csrf:'bad'},body:JSON.stringify(data)});
  return {status:r.status,body:await r.json()};
 },{action,data,csrf});
 for(const p of [a,b])await p.route('**/index.php?api=send',async route=>{
  const {email}=route.request().postDataJSON();
  await p.request.get(base+'/_test_code.php?email='+encodeURIComponent(email));
  await route.fulfill({json:{ok:true}});
 });
 await a.goto(base+'/_test_login.php');
 const saved=await api(a,'save',{content:{title:'Account ownership survives',questions:[{type:'single',prompt:'2+2?',options:['1','2','3','4'],correct:[3],accepted:[],code:'',youtube:'',image:null,seconds:30}]}});assert.equal(saved.status,200);
 await api(a,'logout',{});await a.goto(base+'/?login=1');
 assert.equal((await api(a,'set-password',{password:'not allowed password'})).status,401);
 await a.getByRole('button',{name:'Opprett konto med passord',exact:true}).click();
 await a.getByLabel('E-post i Osloskolen').fill('test@osloskolen.no');await a.getByRole('button',{name:'Send kode',exact:true}).click();
 await a.getByLabel('Engangskode').waitFor();await a.reload();await a.getByLabel('Engangskode').fill('12345678');await a.getByRole('button',{name:'Logg inn',exact:true}).click();
 await a.getByLabel('Nytt passord',{exact:true}).fill('My sufficiently long password');await a.getByLabel('Gjenta passord').fill('My sufficiently long password');
 await a.getByRole('button',{name:'Lagre passord',exact:true}).click();await a.getByText('Passordet er lagret. Andre innlogginger er avsluttet.').waitFor();
 await a.screenshot({path:'/tmp/livequiz-account-mobile.png'});
 await b.goto(base+'/?login=1');
 assert.equal((await api(b,'password-login',{email:'test@osloskolen.no',password:'My sufficiently long password'},false)).status,403);
 await b.getByRole('button',{name:'Logg inn med passord',exact:true}).click();await b.getByLabel('E-post i Osloskolen').fill('test@osloskolen.no');await b.getByLabel('Passord',{exact:true}).fill('wrong');await b.getByRole('button',{name:'Logg inn',exact:true}).click();await b.getByText('Feil e-post eller passord.').waitFor();
 await b.getByLabel('Passord',{exact:true}).fill('My sufficiently long password');await b.getByRole('button',{name:'Logg inn',exact:true}).click();await b.getByText('Account ownership survives',{exact:true}).waitFor();
 await a.getByRole('button',{name:'Logg ut',exact:true}).click();await a.goto(base+'/?login=1');await a.getByRole('button',{name:'Glemt passord?',exact:true}).click();
 await a.getByLabel('E-post i Osloskolen').fill('test@osloskolen.no');await a.getByRole('button',{name:'Send kode',exact:true}).click();await a.getByLabel('Engangskode').fill('12345678');await a.getByRole('button',{name:'Logg inn',exact:true}).click();
 await a.getByLabel('Nytt passord',{exact:true}).fill('A replacement long password');await a.getByLabel('Gjenta passord').fill('A replacement long password');await a.getByRole('button',{name:'Lagre passord',exact:true}).click();await a.getByText('Passordet er lagret. Andre innlogginger er avsluttet.').waitFor();
 const invalid=await b.evaluate(async()=>({boot:await(await fetch('index.php?api=bootstrap')).json(),library:(await fetch('index.php?api=library')).status}));assert.equal(invalid.boot.uid,0);assert.equal(invalid.library,401);
 assert.equal((await api(b,'password-login',{email:'test@osloskolen.no',password:'My sufficiently long password'})).status,422);
 assert.equal((await api(b,'password-login',{email:'test@osloskolen.no',password:'A replacement long password'})).status,200);
 await api(a,'logout',{});await a.goto(base+'/?login=1');
 await a.getByLabel('E-post i Osloskolen').fill('test@osloskolen.no');await a.getByRole('button',{name:'Send kode',exact:true}).click();await a.getByLabel('Engangskode').fill('12345678');await a.getByRole('button',{name:'Logg inn',exact:true}).click();await a.getByText('Account ownership survives',{exact:true}).waitFor();
 assert.deepEqual(errors,[]);console.log('Accounts browser checks passed: registration, reload during verification, password login, email login, recovery, ownership, CSRF and old-session invalidation.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
