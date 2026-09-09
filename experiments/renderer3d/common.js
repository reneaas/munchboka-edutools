export const G = window.MunchScene3D;
export function evaluate(scene, vars) {
    const result=[];
    for(const p of scene.primitives) {
        if(p.type==='mesh') {result.push(p);continue;}
        const points=G.geometry(p,vars,scene.ranges);
        if(!points.length) continue;
        result.push({...p,points,lw:G.evaluate(p.lw,vars),alpha:G.evaluate(p.alpha,vars),
            ...(p.type==='sphere'?{radius:G.evaluate(p.radius,vars)}:{})});
    }
    if(scene.axis) for(let a=0;a<3;a++) {
        const coord=n=>[0,0,0].map((_,i)=>i===a?n:0);
        result.push({type:'vector',points:scene.ranges[a].map(coord),color:'#65747c',lw:1.2});
        result.push({type:'text',points:[coord(scene.ranges[a][1])],text:'$'+'xyz'[a]+'$'});
        if(scene.ticks[a]) for(const t of G.ticks(...scene.ranges[a],scene.steps[a])) {
            const p=coord(t),q=coord(t),r=coord(t);p[(a+1)%3]-=.05;q[(a+1)%3]+=.05;r[(a+1)%3]-=.18;
            result.push({type:'line-segment',points:[p,q],color:'#829098',lw:1});
            result.push({type:'text',points:[r],text:String(t)});
        }
    }
    return result;
}
export function labels(container,items) {
    container.replaceChildren();
    return items.filter(p=>p.type==='text').map(p=>{
        const el=document.createElement('span');el.className='math-label';
        if(p.text.startsWith('$')) katex.render(p.text.replace(/^\$|\$$/g,''),el,{throwOnError:false,trust:false});
        else el.textContent=p.text;
        container.append(el);return {element:el,position:p.points[0]};
    });
}
export function placeLabels(list,project) {
    for(const label of list) {const [x,y]=project(label.position);label.element.style.left=x+'px';label.element.style.top=y+'px';}
}
export function coordinates(camera) {
    const az=camera.azim*Math.PI/180,el=camera.elev*Math.PI/180;
    return [10*Math.cos(el)*Math.cos(az),10*Math.cos(el)*Math.sin(az),10*Math.sin(el)];
}
export function mountPanel(parent,name) {
    const panel=document.createElement('div');panel.className='panel';
    const title=document.createElement('h3');title.textContent=name;
    const viewport=document.createElement('div');viewport.className='viewport';
    const overlay=document.createElement('div');overlay.className='labels';
    const metrics=document.createElement('p');metrics.className='metrics';
    panel.append(title,viewport,metrics);parent.append(panel);
    return {panel,viewport,overlay,metrics};
}
