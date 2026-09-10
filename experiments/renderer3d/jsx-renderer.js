import {labels,placeLabels} from './common.js';
let serial=0;
export class JSXPanel {
    constructor(ui,onCamera) {
        this.ui=ui;ui.viewport.id='compare-jsx-'+serial++;
        this.board=JXG.JSXGraph.initBoard(ui.viewport.id,{boundingbox:[-3.3,3.3,3.3,-3.3],axis:false,
            showCopyright:false,showNavigation:false,keepaspectratio:true,pan:{enabled:false},zoom:{enabled:false},resize:{enabled:false}});
        this.view=this.board.create('view3d',[[-2.5,-2.5],[5,5],[[-2.5,2.5],[-2.5,2.5],[-2.5,2.5]]],{
            r:1,projection:'parallel',axesPosition:'none',depthOrder:{enabled:true},
            az:{slider:{visible:false,min:-2*Math.PI,max:2*Math.PI},pointer:{button:0}},
            el:{slider:{visible:false,min:-Math.PI/2,max:Math.PI/2},pointer:{button:0}},
            bank:{slider:{visible:false}},xPlaneRear:{visible:false},yPlaneRear:{visible:false},zPlaneRear:{visible:false},
            xPlaneFront:{visible:false},yPlaneFront:{visible:false},zPlaneFront:{visible:false}});
        ui.viewport.append(ui.overlay);this.elements=[];this.labelList=[];this.times=[];this.buildTimes=[];this.zoom=1;
        this.board.on('update',()=>{
            if(this.setting) return;
            const azim=90-this.view.az_slide.Value()*180/Math.PI,elev=this.view.el_slide.Value()*180/Math.PI;
            if(this.last && (Math.abs(azim-this.last.azim)>1e-7||Math.abs(elev-this.last.elev)>1e-7))onCamera({azim,elev,zoom:this.zoom});
        });
    }
    update(items) {
        const start=performance.now();this.setting=true;this.board.suspendUpdate();
        for(const el of this.elements)this.view.removeObject(el);this.elements=[];
        const make=(type,parents,attrs={})=>{const el=this.view.create(type,parents,{fixed:true,highlight:false,name:'',withLabel:false,...attrs});this.elements.push(el);return el;};
        const line=(p,color,width,arrow=false,dashed=false)=>make('line3d',p,{strokeColor:color,strokeWidth:width,lastArrow:arrow?{type:2,size:5}:false,dash:dashed?2:0,straightFirst:false,straightLast:false});
        const face=(p,color,alpha)=>make('polygon3d',p,{fillColor:color,fillOpacity:alpha,borders:{strokeWidth:0.2,strokeColor:color},vertices:{visible:false,withLabel:false,name:''}});
        for(const p of items) {
            if(p.type==='text')continue;
            if(p.type==='mesh') {for(const f of p.faces)face(f,p.color,p.alpha);for(const edge of p.edges)line(edge,'#385463',p.lw);}
            else if(['plane','ngon'].includes(p.type))face(p.points.slice(0,-1),p.color,p.alpha);
            else if(p.type==='sphere')make('sphere3d',[p.points[0],p.radius],{fillColor:p.color,gradient:'none',strokeColor:p.color,fillOpacity:p.alpha,center:{visible:false,name:''}});
            else if(p.type==='point')make('point3d',p.points[0],{size:3,fillColor:p.color,strokeColor:p.color});
            else if(['line','line-segment','vector'].includes(p.type))line(p.points,p.color,p.lw,p.type==='vector',p.style && p.style!=='solid');
            else make('curve3d',[0,1,2].map(a=>p.points.map(v=>v[a])),{strokeColor:p.color,strokeWidth:p.lw});
        }
        this.labelList=labels(this.ui.overlay,items);this.board.unsuspendUpdate();this.setting=false;
        this.buildTimes.push(performance.now()-start);
    }
    setCamera(state) {
        this.setting=true;this.zoom=state.zoom;this.last={...state};
        this.view.setView((90-state.azim)*Math.PI/180,state.elev*Math.PI/180,1);
        this.setting=false;
    }
    project(point) {
        const p=this.view.project3DTo2D(point);
        return [this.board.origin.scrCoords[1]+p[1]*this.board.unitX,this.board.origin.scrCoords[2]-p[2]*this.board.unitY];
    }
    render() {
        const start=performance.now(),w=this.ui.viewport.clientWidth,h=this.ui.viewport.clientHeight;
        if(!w||!h)return;
        this.setting=true;
        const sizing=`${w},${h},${this.zoom}`;
        if(this.sizing!==sizing) {
            this.board.resizeContainer(w,h,true);
            this.board.setBoundingBox([-3.3*w/h/this.zoom,3.3/this.zoom,3.3*w/h/this.zoom,-3.3/this.zoom],false);
            this.sizing=sizing;
        }
        placeLabels(this.labelList,p=>this.project(p));this.setting=false;
        this.times.push(performance.now()-start);
        this.ui.metrics.textContent=`${this.elements.length} scene objects · last update ${this.times.at(-1).toFixed(1)} ms · SVG`;
    }
    dispose() {this.setting=true;this.view.setAttribute({depthOrder:{enabled:false}});JXG.JSXGraph.freeBoard(this.board);}
}
