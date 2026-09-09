import * as T from 'three';
import {OrbitControls} from './vendor/three/examples/jsm/controls/OrbitControls.js';
import {Line2} from './vendor/three/examples/jsm/lines/Line2.js';
import {LineGeometry} from './vendor/three/examples/jsm/lines/LineGeometry.js';
import {LineMaterial} from './vendor/three/examples/jsm/lines/LineMaterial.js';
import {labels,placeLabels,coordinates} from './common.js';

// One GPU context for the entire experiment. Each panel receives an immediate
// canvas copy; controls and DOM labels remain local to that panel.
const renderer=new T.WebGLRenderer({antialias:true,alpha:false});
renderer.setClearColor(0xffffff);renderer.setPixelRatio(Math.min(devicePixelRatio,2));
export const gpu={contexts:1,renderer,panels:0};

export class ThreePanel {
    constructor(ui,onCamera) {
        this.ui=ui;this.scene=new T.Scene();this.group=new T.Group();this.scene.add(this.group);
        this.scene.add(new T.AmbientLight(0xffffff,2));
        const light=new T.DirectionalLight(0xffffff,1.5);light.position.set(3,-4,8);this.scene.add(light);
        this.camera=new T.OrthographicCamera(-3.3,3.3,3.3,-3.3,.1,100);this.camera.up.set(0,0,1);
        this.canvas=document.createElement('canvas');this.canvas.setAttribute('aria-label','Three.js interactive 3D figure');
        ui.viewport.append(this.canvas,ui.overlay);this.context=this.canvas.getContext('2d');
        this.controls=new OrbitControls(this.camera,this.canvas);this.controls.enableDamping=false;this.controls.enablePan=false;
        this.controls.minZoom=.4;this.controls.maxZoom=3;
        this.controls.addEventListener('change',()=>{
            if(this.setting) return;
            const p=this.camera.position;
            onCamera({azim:Math.atan2(p.y,p.x)*180/Math.PI,elev:Math.asin(p.z/p.length())*180/Math.PI,zoom:this.camera.zoom});
        });
        this.labelList=[];this.materials=[];this.times=[];this.buildTimes=[];gpu.panels++;
    }
    clear() {
        this.group.traverse(o=>{o.geometry?.dispose();if(o.material)o.material.dispose();});
        this.group.clear();this.materials=[];
    }
    stroke(points,color,width,arrow=false,dashed=false) {
        if(points.length<2) return;
        const geometry=new LineGeometry();geometry.setPositions(points.flat());
        for(const hidden of [false,true]) {
            const material=new LineMaterial({color,linewidth:width,worldUnits:false,
                dashed:hidden||dashed,dashSize:.09,gapSize:.07,
                depthTest:true,depthWrite:false,depthFunc:hidden?T.GreaterDepth:T.LessEqualDepth,
                transparent:hidden,opacity:hidden?.45:1});
            const line=new Line2(hidden?geometry.clone():geometry,material);line.computeLineDistances();
            line.renderOrder=hidden?3:2;this.group.add(line);this.materials.push(material);
        }
        if(arrow) {
            const a=new T.Vector3(...points.at(-2)),b=new T.Vector3(...points.at(-1));
            const dir=b.clone().sub(a).normalize();
            const cone=new T.Mesh(new T.ConeGeometry(.055,.18,12),new T.MeshBasicMaterial({color}));
            cone.position.copy(b.clone().addScaledVector(dir,-.09));cone.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),dir);
            this.group.add(cone);
        }
    }
    face(faces,color,alpha) {
        const vertices=[];
        for(const face of faces) for(let i=1;i<face.length-1;i++) vertices.push(...face[0],...face[i],...face[i+1]);
        const geometry=new T.BufferGeometry();geometry.setAttribute('position',new T.Float32BufferAttribute(vertices,3));geometry.computeVertexNormals();
        const material=new T.MeshLambertMaterial({color,side:T.DoubleSide,transparent:alpha<1,opacity:alpha,depthWrite:alpha>=1,
            polygonOffset:true,polygonOffsetFactor:1,polygonOffsetUnits:1});
        this.group.add(new T.Mesh(geometry,material));
    }
    update(items) {
        const start=performance.now();this.clear();this.labelList=labels(this.ui.overlay,items);
        for(const p of items) {
            if(p.type==='text') continue;
            if(p.type==='mesh') {this.face(p.faces,p.color,p.alpha);for(const edge of p.edges)this.stroke(edge,'#385463',p.lw);}
            else if(['plane','ngon'].includes(p.type)) {this.face([p.points.slice(0,-1)],p.color,p.alpha);this.stroke(p.points,p.color,1);}
            else if(p.type==='sphere'||p.type==='point') {
                const mesh=new T.Mesh(new T.SphereGeometry(p.type==='point'?.05:p.radius,48,24),new T.MeshLambertMaterial({color:p.color,transparent:p.alpha<1,opacity:p.type==='point'?1:p.alpha,depthWrite:p.type==='point'||p.alpha>=1}));
                mesh.position.set(...p.points[0]);this.group.add(mesh);
            } else {
                let part=[];
                for(const point of p.points) {if(point.every(Number.isFinite))part.push(point);else{this.stroke(part,p.color,p.lw);part=[];}}
                this.stroke(part,p.color,p.lw,p.type==='vector',p.style && p.style!=='solid');
            }
        }
        this.buildTimes.push(performance.now()-start);
    }
    setCamera(state) {
        this.setting=true;
        this.camera.position.set(...coordinates(state));this.camera.zoom=state.zoom;
        this.camera.lookAt(0,0,0);this.camera.updateProjectionMatrix();this.controls.update();this.setting=false;
    }
    project(point) {
        const p=new T.Vector3(...point).project(this.camera);
        return [(p.x+1)*this.ui.viewport.clientWidth/2,(1-p.y)*this.ui.viewport.clientHeight/2];
    }
    render() {
        const start=performance.now(),w=this.ui.viewport.clientWidth,h=this.ui.viewport.clientHeight;
        if(!w||!h) return;
        this.camera.left=-3.3*w/h;this.camera.right=3.3*w/h;this.camera.updateProjectionMatrix();
        renderer.setSize(w,h,false);
        for(const m of this.materials)m.resolution.set(w,h);
        renderer.render(this.scene,this.camera);
        if(this.canvas.width!==renderer.domElement.width||this.canvas.height!==renderer.domElement.height) {
            this.canvas.width=renderer.domElement.width;this.canvas.height=renderer.domElement.height;
        }
        this.context.drawImage(renderer.domElement,0,0);
        placeLabels(this.labelList,p=>this.project(p));
        this.times.push(performance.now()-start);
        this.ui.metrics.textContent=`${this.group.children.length} draw objects · last update ${this.times.at(-1).toFixed(1)} ms · shared GPU context`;
    }
    dispose() {this.controls.dispose();this.clear();this.ui.overlay.replaceChildren();gpu.panels--;}
}
