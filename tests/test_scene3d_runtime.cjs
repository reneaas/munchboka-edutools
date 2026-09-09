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
