/* Geometry and arithmetic shared by the browser runtime and Node tests. */
(function (root) {
    "use strict";
    const EPS = 1e-10;
    const add = (a, b) => a.map((x, i) => x + b[i]);
    const sub = (a, b) => a.map((x, i) => x - b[i]);
    const scale = (a, s) => a.map(x => x * s);
    const dot = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
    const norm = a => Math.hypot(...a);
    const unit = a => { const n = norm(a); if (n < EPS) throw Error("Zero direction"); return scale(a, 1 / n); };
    const cross = (a, b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
    const perpendicular = a => unit(cross(a, Math.abs(a[0]) < 0.8 ? [1,0,0] : [0,1,0]));
    const funcs = Object.fromEntries(["sqrt","exp","log","sin","cos","tan","asin","acos","atan","sinh","cosh","tanh"].map(k => [k, Math[k]]));
    funcs.Abs = Math.abs;
    function evaluate(tree, vars) {
        if (typeof tree === "number") return tree;
        const [op, ...args] = tree;
        if (op === "var") {
            if (!Object.hasOwn(vars, args[0])) throw Error("Unknown variable " + args[0]);
            return vars[args[0]];
        }
        const v = args.map(a => evaluate(a, vars));
        if (Object.hasOwn(funcs, op)) return funcs[op](...v);
        switch (op) {
        case "+": return v[0]+v[1]; case "-": return v[0]-v[1];
        case "*": return v[0]*v[1]; case "/": return v[0]/v[1];
        case "**": return v[0]**v[1]; case "neg": return -v[0];
        default: throw Error("Unknown expression operator");
        }
    }
    function clippedLine(p, d, ranges) {
        if (norm(d) < EPS) return [];
        let lo = -Infinity, hi = Infinity;
        for (let i = 0; i < 3; i++) {
            if (Math.abs(d[i]) < EPS) { if (p[i] < ranges[i][0] || p[i] > ranges[i][1]) return []; }
            else {
                const a = (ranges[i][0]-p[i])/d[i], b = (ranges[i][1]-p[i])/d[i];
                lo = Math.max(lo, Math.min(a,b)); hi = Math.min(hi, Math.max(a,b));
            }
        }
        return lo > hi ? [] : [add(p,scale(d,lo)), add(p,scale(d,hi))];
    }
    function planePolygon(coeff, ranges) {
        const n = coeff.slice(0,3); unit(n);
        const corners = Array.from({length:8}, (_, k) => ranges.map((r,i) => r[(k>>i)&1]));
        const points = [];
        const insert = p => { if (!points.some(q => norm(sub(p,q)) < EPS)) points.push(p); };
        corners.forEach((a,k) => {
            for (let i=0; i<3; i++) {
                if ((k>>i)&1) continue;
                const b = corners[k|(1<<i)], fa = dot(n,a)+coeff[3], fb = dot(n,b)+coeff[3];
                if (Math.abs(fa)<EPS) insert(a);
                if (Math.abs(fb)<EPS) insert(b);
                if (fa*fb<0) insert(add(a,scale(sub(b,a),fa/(fa-fb))));
            }
        });
        if (points.length < 3) return [];
        const c = scale(points.reduce(add, [0,0,0]), 1/points.length), u = perpendicular(unit(n)), v = cross(unit(n),u);
        points.sort((a,b) => Math.atan2(dot(sub(a,c),v),dot(sub(a,c),u))-Math.atan2(dot(sub(b,c),v),dot(sub(b,c),u)));
        return [...points, points[0]];
    }
    function geometry(item, vars, ranges) {
        const e = t => evaluate(t,vars), v = t => t.map(e);
        let points;
        switch (item.type) {
        case "point": points = [v(item.coords)]; break;
        case "text": points = [add(v(item.at), v(item.offset))]; break;
        case "sphere": {
            const radius = e(item.radius);
            if (!(radius > EPS) || !Number.isFinite(radius)) return [];
            points = [v(item.center)]; break;
        }
        case "line": {
            const a = v(item.start), d = item.direction ? v(item.direction) : sub(v(item.end),a);
            points = clippedLine(a,d,ranges); break;
        }
        case "vector": case "line-segment": points = [v(item.start),v(item.end)]; break;
        case "plane": {
            if (item.coefficients) points = planePolygon(v(item.coefficients), item.ranges.map(v));
            else {
                const n = unit(v(item.normal)), u = perpendicular(n), w = cross(n,u), c = v(item.point), span = v(item.span);
                if (span.some(s => s <= EPS)) return [];
                points = [[-1,-1],[1,-1],[1,1],[-1,1],[-1,-1]].map(([a,b]) => add(c,add(scale(u,a*span[0]/2),scale(w,b*span[1]/2))));
            }
            break;
        }
        case "right-angle": case "angle": {
            const c = v(item.at), a = item.to1 ? sub(v(item.to1),c) : v(item.dir1), b = item.to2 ? sub(v(item.to2),c) : v(item.dir2);
            const u = unit(a), w = unit(b); let r = e(item.radius);
            if (!(r > EPS)) return [];
            if (item.type === "right-angle") {
                if (Math.abs(dot(u,w)) > 1e-7) return [];
                if (item.to1) r = Math.min(r,norm(a),norm(b));
                points = [add(c,scale(u,r)),add(c,scale(add(u,w),r)),add(c,scale(w,r))];
            } else {
                const cosine = Math.max(-1,Math.min(1,dot(u,w))), theta = Math.acos(cosine);
                if (theta < EPS) return [];
                const tangent = norm(sub(w,scale(u,cosine))) < EPS ? perpendicular(u) : unit(sub(w,scale(u,cosine)));
                points = Array.from({length:65}, (_,i) => add(c,scale(add(scale(u,Math.cos(theta*i/64)),scale(tangent,Math.sin(theta*i/64))),r)));
            }
            break;
        }
        case "curve": {
            const [lo,hi] = v(item.range);
            points = Array.from({length:item.samples},(_,i) => item.coordinates.map(t => evaluate(t,{...vars,t:lo+(hi-lo)*i/(item.samples-1)})));
            // Nonfinite samples break the path rather than joining across a singularity.
            return points.map(p => p.every(Number.isFinite) ? p : [NaN,NaN,NaN]);
        }
        case "ngon": points = item.points.map(v); points.push(points[0]); break;
        default: throw Error("Unsupported primitive " + item.type);
        }
        return points.every(p => p.every(Number.isFinite)) ? points : [];
    }
    function ticks(lo,hi,step,grid=false) {
        const result = [];
        for (let k=Math.ceil(lo/step); k<=Math.floor(hi/step) && result.length<201; k++) {
            const x=k*step;
            if (grid || (Math.abs(x)>EPS && x>lo+EPS && x<hi-EPS)) result.push(x);
        }
        return result;
    }
    const api = {evaluate,geometry,ticks,clippedLine,planePolygon,add,sub,dot};
    if (typeof module !== "undefined" && module.exports) module.exports = api;
    else root.MunchScene3D = api;
})(typeof window !== "undefined" ? window : globalThis);
