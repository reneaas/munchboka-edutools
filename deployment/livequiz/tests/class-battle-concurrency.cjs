// Run only against the disposable MySQL fixture described in concurrency-testing.md.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const base = process.env.LIVEQUIZ_BASE || 'http://127.0.0.1:8878';
assert.equal(new URL(base).hostname, '127.0.0.1');
const n = Number(process.env.STUDENTS_PER_CLASS || 30);
assert(Number.isInteger(n) && n >= 3 && n <= 100);
const samples = [], statuses = {}, checks = [];
const sleep = ms => new Promise(r => setTimeout(r, ms));
let active=0; const waiting=[];
async function slot(){if(active>=48)await new Promise(r=>waiting.push(r));else active++;}
function release(){const next=waiting.shift();if(next)next();else active--;}
class Client {
  constructor() { this.cookie = ''; this.headers = {'X-Player-Token':require('node:crypto').randomBytes(32).toString('hex')}; }
  async request(api, body, expected = 200) {
    await slot();
    const start = performance.now();
    try {
    const response = await fetch(base + '/index.php?api=' + api, {
      signal: AbortSignal.timeout(30000),
      method: body === undefined ? 'GET' : 'POST',
      headers: {Cookie:this.cookie, 'Content-Type':'application/json', 'X-CSRF-Token':this.csrf || '', ...this.headers},
      body: body === undefined ? undefined : JSON.stringify(body)
    });
    const cookie = response.headers.get('set-cookie');
    if (cookie) this.cookie = cookie.split(';')[0];
    const data = await response.json();
    samples.push({api:api.split('&')[0], ms:performance.now()-start});
    statuses[response.status] = (statuses[response.status] || 0) + 1;
    if (expected !== null) assert.equal(response.status, expected, JSON.stringify(data));
    return {status:response.status, data};
    } finally {release();}
  }
  async init(teacher=false) {
    if (teacher) {
      const r=await fetch(base+'/_test_login.php',{redirect:'manual'});
      this.cookie=r.headers.get('set-cookie').split(';')[0];
    }
    this.csrf=(await this.request('bootstrap')).data.csrf;
    return this;
  }
}
(async()=>{
  const probes=await Promise.all(Array.from({length:36},async()=> {
    const r=await fetch(base+'/_simulation.php'); const d=await r.json();
    assert.equal(d.fixture,'isolated-mysql-concurrency');return d.pid;
  }));
  const workers=[...new Set(probes)];assert(workers.length>1,'Requires multiple PHP workers');
  const main=await new Client().init(true);
  const q={type:'single',prompt:'Simulation',seconds:60,options:['Correct','Wrong'],correct:[0]};
  const quiz=(await main.request('save',{content:{title:'Concurrency simulation',questions:[q,q]}})).data;
  const room=(await main.request('create',{id:quiz.id})).data;
  const state=c=>c.request('state&room='+room.room+(c===main||c.headers['X-Cohost-Token']?'&host=1':'')).then(r=>r.data);
  const control=async command=>{const s=await state(main);return main.request('control',{room:room.room,run:s.run,version:s.version,command,game:'classbattle'});};
  await control('configure');
  const teachers=[main],codes=[room.pin];
  for(let i=1;i<3;i++){
    const key=(await main.request('battle-manage',{room:room.room,command:'invite'})).data.key;
    const co=await new Client().init();co.headers['X-Cohost-Token']=key;
    const claims=await Promise.all(Array.from({length:8},()=>co.request('battle-join',{room:room.room,key,name:'Class '+i})));
    assert.equal(new Set(claims.map(r=>r.data.class)).size,1);
    teachers.push(co);codes.push((await state(co)).pin);
  }
  checks.push('Concurrent invitation redemption creates one class');
  const students=await Promise.all(Array.from({length:3*n},async(_,i)=>{
    const c=await new Client().init();c.group=Math.floor(i/n);c.index=i%n;
    const joined=(await c.request('join',{pin:codes[c.group],name:'Student '+i})).data;
    assert.equal(joined.room,room.room);return c;
  }));
  assert.equal((await state(main)).players,3*n);
  for(const co of teachers.slice(1)){
    const s=await state(co);assert.equal(s.lobby_players.length,n);assert.equal(s.battle.results.length,1);
    await co.request('control',{room:room.room,command:'finish'},403);
  }
  checks.push('Simultaneous joins preserve all students; co-host scope and control permissions');
  await control('next');
  while((await state(main)).state!=='QUESTION_ACTIVE')await sleep(100);
  const late=await new Client().init();
  assert.notEqual((await late.request('join',{pin:codes[1],name:'Late'},null)).status,200);
  for(let index=0;index<2;index++){
    const snapshots=await Promise.all(teachers.map(state));
    assert.equal(new Set(snapshots.map(s=>s.deadline)).size,1);
    // Three polling rounds overlap the answer burst. One third of clients have
    // 250ms simulated outbound latency; disconnected clients skip polling.
    const polling=Promise.all(students.filter((_,i)=>i%5).map(async c=>{
      for(let round=0;round<3;round++){await state(c);await sleep(150);}
    }));
    await Promise.all(students.map(async c=>{
      if(c.group===2)await sleep(250);
      const answer=[c.index < Math.floor(n*(c.group+1)/3) ? 0 : 1];
      const body={room:room.room,run:0,index,answer};
      await Promise.all([c.request('answer',body),c.request('answer',body),c.request('answer',body)]);
      // Treat the original response as lost; reconnect and retry a conflicting answer.
      await c.request('answer',{...body,answer:answer[0]===0?[1]:[0]});
    }));
    await polling;
    const s=await state(main);assert.equal(s.answers,3*n);assert.equal(s.state,'QUESTION_RESULTS');
    for(let group=0;group<3;group++){
      const cls=s.battle.classes.find(x=>x.name===(group===0?'Class A':'Class '+group));
      assert.equal(cls.count,n);assert.equal(cls.total,Math.floor(n*(group+1)/3)*1000*(index+1));
      assert.equal(cls.score,cls.total/n);
    }
    const views=await Promise.all(teachers.map(state));
    for(const v of views)assert.deepEqual(v.battle.classes,s.battle.classes);
    const reconnected=await state(students[0]);assert.equal(reconnected.state,'QUESTION_RESULTS');
    await control('leaderboard');await control('next');
    if(index===0)while((await state(main)).state!=='QUESTION_ACTIVE')await sleep(100);
  }
  assert.equal((await state(main)).state,'QUIZ_FINISHED');
  checks.push('Shared deadlines and standings across three classrooms',
    'Concurrent answers and polling; triple submissions score once',
    'Lost-response retry with conflicting answer preserves original score',
    'Late joins rejected; disconnected clients resume current state',
    'Exact class totals and averages across two questions');
  const metrics={};
  for(const api of [...new Set(samples.map(s=>s.api))]){
    const values=samples.filter(s=>s.api===api).map(s=>s.ms).sort((a,b)=>a-b);
    metrics[api]={requests:values.length,p50_ms:Math.round(values[Math.floor(values.length*.5)]),p95_ms:Math.round(values[Math.floor(values.length*.95)]),max_ms:Math.round(values.at(-1))};
  }
  const report={max_in_flight:48,students:3*n,classes:3,questions:2,worker_count:workers.length,statuses,checks,metrics};
  console.log(JSON.stringify(report,null,2));
  if(process.env.REPORT_PATH)fs.writeFileSync(process.env.REPORT_PATH,JSON.stringify(report,null,2)+'\n');
})().catch(e=>{console.error(e);process.exitCode=1;});
