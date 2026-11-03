const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM_PATH});
 try{
 const host=await browser.newPage(),student=await browser.newPage({viewport:{width:390,height:844}}),base=process.env.LIVEQUIZ_BASE||'http://127.0.0.1:8798';
 await host.goto(base+'/_test_login.php');
 for(const [type,wrong] of [['single',false],['multi',false],['text',false],['single',true]]){
  const room=await host.evaluate(async type=>{
   const boot=await(await fetch('index.php?api=bootstrap')).json();
   const post=async(action,data)=>(await(await fetch('index.php?api='+action,{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':boot.csrf},body:JSON.stringify(data)})).json());
   const quiz=await post('save',{content:{title:'Participant results '+type,questions:[{type,prompt:'Velg riktig svar',code:'',youtube:'',image:null,seconds:120,options:['A','B','C','D'],correct:type==='multi'?[0,1]:[0],accepted:['fire','4']}]}});
   return await post('create',{id:quiz.id});
  },type);
  await host.goto(base+'/?host='+room.room);await host.locator('.pin').waitFor();
  await student.goto(base+'/?pin='+room.pin);await student.getByLabel('Kallenavn').fill('Elev');await student.getByRole('button',{name:'Bli med',exact:true}).click();await student.getByText('Du er med!',{exact:true}).waitFor();
  await host.getByRole('button',{name:'Start første spørsmål'}).click();await student.locator('.active-question-modal').waitFor();
  if(type==='text')await host.getByRole('button',{name:'Vis fasit nå'}).click();
  else{
   for(const answer of type==='multi'?['A','B']:[wrong?'C':'A'])await student.locator(`.answer-option:has(.rich:text-is("${answer}"))`).locator('input').check();
   await student.getByRole('button',{name:'Send svar',exact:true}).click();
  }
  await student.getByRole('heading',{name:'Fasit',exact:true}).waitFor();await host.getByRole('heading',{name:'Svarfordeling',exact:true}).waitFor();
  assert.equal(await host.locator('.results-modal .question-media,.results-modal .option-grid,.results-modal .qcard-head').count(),0);
  await student.locator('.results-modal').getByText('Velg riktig svar',{exact:true}).waitFor();
  assert.equal(await student.locator('.chart,.chart-count').count(),0);
  assert.ok(await host.locator('.chart-row').count()>0);
  if(type==='text'){
   await student.getByText('Riktig svar: fire · 4',{exact:true}).waitFor();
   await student.getByText('Du fikk 0 poeng. Du svarte ikke på dette spørsmålet.',{exact:true}).waitFor();
  }else{
   await student.getByText(`Du fikk ${wrong?0:1000} poeng.`,{exact:true}).waitFor();
   assert.equal(await student.locator('.option-card.correct').count(),type==='multi'?2:1);
   await student.locator('.personal-answer-result.'+(wrong?'wrong':'correct')).getByText(wrong?'Feil svar':'Riktig svar!',{exact:true}).waitFor();
   await student.locator('.personal-answer-result').getByText(wrong?'C':'A',{exact:true}).waitFor();
  }
  const points=await student.locator('.results-analysis .result').boundingBox();assert.ok(points.y>=0&&points.y+points.height<=844);
  await student.reload();await student.getByRole('heading',{name:'Fasit',exact:true}).waitFor();assert.equal(await student.locator('.chart').count(),0);
 }
 console.log('Participant results passed: single/multi/text answers, correct, wrong and unanswered feedback, mobile visibility, reload, and teacher-only charts.');
 }finally{await browser.close();}
})();
