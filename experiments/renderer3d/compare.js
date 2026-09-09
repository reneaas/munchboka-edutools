import {evaluate,mountPanel} from './common.js';
import {ThreePanel,gpu} from './three-renderer.js';
import {JSXPanel} from './jsx-renderer.js';
const data=await (await fetch('./cases.json')).json();
const comparisons=[];
for(const entry of data) {
    const section=document.createElement('section');section.id=entry.id;
    const heading=document.createElement('h2');heading.textContent=entry.title;
    const question=document.createElement('p');question.className='question';question.textContent=entry.question;
    const pair=document.createElement('div');pair.className='pair';
    const controls=document.createElement('div');controls.className='controls';
    section.append(heading,question,pair,controls);document.querySelector('main').append(section);
    const vars=Object.fromEntries(entry.scene.sliders.map(s=>[s.name,s.min+(s.max-s.min)*s.initial/(s.count-1)]));
    let state={azim:-55,elev:25,zoom:1},pending=false;
    const panels=[],cameraInputs=[];
    function render() {
        if(pending)return;pending=true;
        requestAnimationFrame(()=>{pending=false;for(const p of panels){p.setCamera(state);p.render();}});
    }
    function camera(next) {state={...next};for(const c of cameraInputs){c.input.value=state[c.key];c.output.textContent=state[c.key].toFixed(0);}render();}
    panels.push(new JSXPanel(mountPanel(pair,'JSXGraph · native polygons'),camera));
    panels.push(new ThreePanel(mountPanel(pair,'Three.js · depth buffer'),camera));
    function geometry() {const items=evaluate(entry.scene,vars);for(const p of panels)p.update(items);render();}
    function slider(name,min,max,step,start,onChange) {
        const wrap=document.createElement('label'),title=document.createElement('span'),input=document.createElement('input'),output=document.createElement('output');
        title.textContent=name;input.type='range';input.min=min;input.max=max;input.step=step;input.value=start;input.setAttribute('aria-label',name);output.textContent=start;
        input.addEventListener('input',()=>{output.textContent=Number(input.value).toFixed(2);onChange(+input.value);});
        wrap.append(title,input,output);controls.append(wrap);return {input,output};
    }
    cameraInputs.push({key:'azim',...slider('Azimuth',-180,180,1,-55,v=>camera({...state,azim:v}))});
    cameraInputs.push({key:'elev',...slider('Elevation',-80,80,1,25,v=>camera({...state,elev:v}))});
    for(const s of entry.scene.sliders)slider(s.name,s.min,s.max,(s.max-s.min)/(s.count-1),vars[s.name],v=>{vars[s.name]=v;geometry();});
    for(const [name,action] of [['Reset',()=>camera({azim:-55,elev:25,zoom:1})],['Zoom in',()=>camera({...state,zoom:Math.min(3,state.zoom*1.2)})],['Zoom out',()=>camera({...state,zoom:Math.max(.4,state.zoom/1.2)})]]) {
        const b=document.createElement('button');b.textContent=name;b.onclick=action;controls.append(b);
    }
    const observer=new ResizeObserver(render);for(const p of panels)observer.observe(p.ui.viewport);
    geometry();
    comparisons.push({id:entry.id,panels,vars,camera,geometry,get state(){return state;},dispose(){observer.disconnect();panels.forEach(p=>p.dispose());}});
}
window.comparison={cases:comparisons,gpu};
await document.fonts.ready;
for(const c of comparisons)c.camera(c.state);
document.querySelector('#health').textContent=`Ready · ${comparisons.length} matched pairs · ${gpu.contexts} shared WebGL context · all assets local`;
