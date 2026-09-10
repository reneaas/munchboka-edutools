const {test} = require('node:test');
const assert = require('node:assert/strict');
const G = require('../src/munchboka_edutools/static/js/interactive3d/scene.js');
const ranges = [[-2,2],[-2,2],[-2,2]];

test('line clips against all six sides and handles parallel misses',()=>{
    assert.deepEqual(G.clippedLine([0,0,0],[1,2,0],ranges),[[-1,-2,0],[1,2,0]]);
    assert.deepEqual(G.clippedLine([0,3,0],[1,0,0],ranges),[]);
    assert.deepEqual(G.clippedLine([0,0,0],[0,0,0],ranges),[]);
});
test('vertical and oblique plane polygons satisfy equations and bounds',()=>{
    for(const c of [[1,0,0,-1],[1,2,3,-1]]) {
        const points=G.planePolygon(c,ranges);
        assert.ok(points.length>=4);
        for(const p of points) {
            assert.ok(Math.abs(G.dot(c.slice(0,3),p)+c[3])<1e-9);
            assert.ok(p.every(v=>v>=-2 && v<=2));
        }
    }
});
test('angle arcs remain in their 3D plane and on their circle',()=>{
    const points=G.geometry({type:'angle',at:[1,2,3],dir1:[1,0,0],dir2:[0,1,1],radius:0.5},{},ranges);
    for(const p of points) {
        const d=G.sub(p,[1,2,3]);
        assert.ok(Math.abs(Math.hypot(...d)-0.5)<1e-9);
        assert.ok(Math.abs(d[1]-d[2])<1e-9);
    }
});
test('right angle disappears when slider makes directions nonorthogonal',()=>{
    const item={type:'right-angle',at:[0,0,0],dir1:[1,0,0],dir2:[['var','a'],1,0],radius:0.3};
    assert.equal(G.geometry(item,{a:0},ranges).length,3);
    assert.deepEqual(G.geometry(item,{a:1},ranges),[]);
});
test('tick and grid conventions preserve origin and endpoint rules',()=>{
    assert.deepEqual(G.ticks(-2,2,1),[-1,1]);
    assert.deepEqual(G.ticks(-2,2,1,true),[-2,-1,0,1,2]);
});
test('live expression values and invalid spheres',()=>{
    assert.equal(G.evaluate(['**',['var','a'],2],{a:3}),9);
    assert.deepEqual(G.geometry({type:'sphere',center:[0,0,0],radius:['var','r']},{r:-1},ranges),[]);
});

const drawing=(type,fields)=>({type,color:'#000000',lw:1.5,alpha:.35,...fields});
const resolve=(items,vars={})=>G.objects({primitives:items,ranges,axis:false,grid:false},vars);
test('normal segments join a point to its plane and skew lines orthogonally',()=>{
    const plane=resolve([drawing('normal-segment',{point:[1,2,3],coefficients:[1,1,1,-3]})]).items[0].points;
    assert.ok(Math.abs(plane[1].reduce((s,x)=>s+x,0)-3)<1e-9);
    const lines=resolve([drawing('normal-segment',{point1:[0,0,0],direction1:[1,0,0],point2:[0,2,3],direction2:[0,1,0]})]).items[0].points;
    assert.deepEqual(lines,[[0,0,0],[0,0,3]]);
    assert.equal(resolve([drawing('normal-segment',{point:[0,0,1],coefficients:[0,0,0,1]})]).errors.length,1);
});
test('regular prisms rebuild topology from slider values and use radian rotations',()=>{
    const prism=drawing('prism',{center:[0,0,0],radius:1,sides:['var','n'],rotation:Math.PI/2,extrusion:[0,0,2]});
    for(const n of [3,5]) {
        const mesh=resolve([prism],{n}).items[0];assert.equal(mesh.faces.length,n+2);assert.equal(mesh.edges.length,3*n);
        assert.ok(Math.abs(mesh.faces[0][0][1]-1)<1e-9);assert.equal(mesh.faces[1][0][2],2);
    }
    assert.equal(resolve([prism],{n:3.5}).errors.length,1);
});
test('solids revolve around x and preserve the absolute radius convention',()=>{
    const mesh=resolve([drawing('solid-of-revolution',{expression:-2,range:[0,3],samples:4,radialSamples:8})]).items[0];
    assert.equal(mesh.faces.length,24);
    for(const point of mesh.faces.flat())assert.ok(Math.abs(Math.hypot(point[1],point[2])-2)<1e-9);
});
test('repeat topology responds to sliders and expansion is bounded',()=>{
    const child=drawing('point',{coords:[['var','i'],0,0]});
    const loop={type:'repeat',variable:'i',lower:1,upper:['var','n'],child};
    assert.equal(resolve([loop],{n:4}).items.length,4);
    assert.equal(resolve([loop],{n:2}).items.length,2);
    assert.equal(resolve([loop],{n:1.5}).errors.length,1);
    const nested={type:'repeat',variable:'j',lower:1,upper:999,child:loop};
    const result=resolve([nested],{n:999});assert.ok(result.errors.length);assert.ok(result.items.length<1000);
});
test('singular curves break paths and live text interpolation remains literal',()=>{
    const curve=drawing('curve',{range:[-1,1],samples:3,coordinates:[['var','t'],['/',1,['var','t']],0]});
    const result=resolve([curve]);assert.ok(Number.isNaN(result.items[0].points[1][1]));
    const text=drawing('text',{at:[0,0,0],offset:[0,0,0],fontsize:12,text:'<b>$a={a:.1f}$</b>'});
    assert.equal(resolve([text],{a:1.23}).items[0].text,'<b>$a=1.2$</b>');
});
