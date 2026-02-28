# `plot` directive

:::{plot}
width: 70%
let: a = 4
function: x + 8 / x - 4, (0, 10), f, blue
point: (0, 0)
point: (a, 0)
point: (a, f(a))
point: (0, f(a))
polygon: (0, 0), (a, 0), (a, f(a)), (0, f(a)), teal, 0.2
ymin: -1
xmin: -0.5
xmax: 7
ymax: 4
ticks: off
text: a, f(a), "$(a, f(a))$", bottom-right
:::


:::{plot}
width: 70%
let: a = 2.5
function: 3 * x / (x**3 + 4), (0, 10), f, blue
point: (0, 0)
point: (a, 0)
point: (a, f(a))
point: (0, f(a))
polygon: (0, 0), (a, 0), (a, f(a)), (0, f(a)), teal, 0.3
ymin: -0.2
xmin: -0.5
xmax: 6
ymax: 1
ticks: off
text: a, f(a), "$(a, f(a))$", top-right
:::




:::{plot}
width: 70%
xlabel: $t/\mathrm{min}$
ylabel: $T^\circ\mathrm{C}$
function: 2 * x - 10, (0, 5)
function: 0, (5, 15)
function: 4.18 * 0.5 * (x - 15), (5, 15)
:::


:::{plot}
width: 70%
ticks: off
axis: equal
let: Ax = 1
let: Ay = 1
let: ux = 2
let: uy = 1
let: vx = 3
let: vy = 3
let: Bx = Ax + ux
let: By = Ay + uy
let: Cx = Ax + vx
let: Cy = Ay + vy
point: (Ax, Ay)
point: (Bx, By)
point: (Cx, Cy)
vector: (Ax, Ay), (Bx, By), blue
vector: (Ax, Ay), (Cx, Cy), red
text: Ax, Ay - 0.1, "$A$", bottom-center
text: Bx + 0.1, By, "$B({Bx}, {By})$", bottom-right
text: Cx + 0.1, Cy, "$C({Cx}, {Cy})$", top-right
let: k = 1.2
line-segment: (Ax - k*ux, Ay - k*uy), (Bx + k*ux, By + k*uy), dashed, gray
text: 0.5 * (Ax + Bx), 0.5 * (Ay + By) - 0.2, "$\vec{u} = [{ux}, {uy}]$", bottom-right
text: 0.5 * (Ax + Cx) - 0.2, 0.5 * (Ay + Cy), "$\vec{v}$", top-left
line-segment: (Bx, By), (Cx, Cy), solid, gray 
let: ux_tverr = -uy
let: uy_tverr = ux
let: u_norm = (ux**2 + uy**2)**0.5
let: hx = ((Cx - Ax) * ux_tverr + (Cy - Ay) * uy_tverr) / u_norm * ux_tverr / u_norm
let: hy = ((Cx - Ax) * uy_tverr + (Cy - Ay) * ux_tverr) / u_norm * uy_tverr / u_norm
line-segment: (Cx, Cy), (Cx - hx, Cy - hy), dotted, gray
let: dsx = 0.25 * ux / u_norm
let: dsy = 0.25 * uy / u_norm
let: drx = -dsy
let: dry = dsx
line-segment: (Cx - hx - dsx, Cy - hy - dsy), (Cx - hx - dsx + drx, Cy - hy - dsy + dry), solid, teal
line-segment: (Cx - hx - dsx + drx, Cy - hy - dsy + dry), (Cx - hx + drx, Cy - hy + dry), solid, teal
fill-polygon: (Cx - hx, Cy - hy), (Cx - hx - dsx, Cy - hy - dsy), (Cx - hx - dsx + drx, Cy - hy - dsy + dry), (Cx - hx + drx, Cy - hy + dry), teal, 0.3
let: Dx = Cx - hx
let: Dy = Cy - hy
point: (Dx, Dy)
text: Dx + 0.1, Dy, "$D$", bottom-right
let: Ex = Cx - ux
let: Ey = Cy - uy
point: (Ex, Ey)
text: Ex - 0.1, Ey, "$E$", top-left
line-segment: (Cx, Cy), (Ex, Ey), dashdot, gray
line-segment: (Ax, Ay), (Ex, Ey), dashdot, gray
:::




:::{plot}
width: 70%
ticks: off
axis: equal
let: Ax = 3
let: Ay = 2
let: Bx = 9
let: By = 2
let: ux = 3
let: uy = 7
let: Cx = Ax + ux
let: Cy = Ay + uy
let: vx = Bx - Ax
let: vy = By - Ay
let: Dx = Cx + vx
let: Dy = Cy + vy
let: Mx = 0.5 * (Ax + Bx)
let: My = 0.5 * (Ay + By)
point: (Ax, Ay)
point: (Bx, By)
point: (Cx, Cy)
point: (Dx, Dy)
point: (Mx, My)
text: Ax - 0.1, Ay, "$A({Ax}, {Ay})$", bottom-left
text: Bx + 0.1, By, "$B({Bx}, {By})$", bottom-right
text: Cx, Cy, "$C$", top-left
text: Dx + 0.1, Dy, "$D$", top-right
text: Mx - 0.1, My + 0.2, "$M$", top-left
vector: (Ax, Ay), (Bx, By), blue
vector: (Ax, Ay), (Cx, Cy), red
line-segment: (Bx, By), (Cx, Cy), solid, black
line-segment: (Cx, Cy), (Dx, Dy), dashed, black
line-segment: (Bx, By), (Dx, Dy), dashed, black
line-segment: (Cx, Cy), (Mx, My), dashed, gray
let: ds = 0.6
line-segment: (Mx + ds, My), (Mx + ds, My + ds), solid, teal
line-segment: (Mx + ds, My + ds), (Mx, My + ds), solid, teal
fill-polygon: (Mx, My), (Mx + ds, My), (Mx + ds, My + ds), (Mx, My + ds), teal, 0.3
text: 0.5 * (Ax + Cx), 0.5 * (Ay + Cy) + 0.2, "$\overrightarrow{AC} = [3, 7]$", top-left
text: 0.5 * (Ax + Bx), 0.5 * (Ay + By) - 0.2, "$\vec{u}$", bottom-center
:::


:::{plot}
width: 70%
ticks: off
figsize: (6, 6)
xmin: -0.5
xmax: 6
ymin: -2.5
ymax: 4
let: Ax = 1
let: Ay = 2
let: Bx = 4
let: By = 3
let: vx = 2
let: vy = -4
let: Ex = 5
let: Ey = 2
let: Cx = Ax + vx
let: Cy = Ay + vy
let: Dx = 0.5 * (Ax + Cx)
let: Dy = 0.5 * (Ay + Cy)
point: (Ax, Ay)
point: (Bx, By)
point: (Cx, Cy)
point: (Dx, Dy)
point: (Ex, Ey)
text: Ax, Ay, "$A({Ax}, {Ay})$", top-left
text: Bx, By, "$B({Bx}, {By})$", center-right
text: Cx, Cy, "$C$", bottom-right
text: Dx, Dy - 0.2, "$D$", bottom-center
text: Ex, Ey, "$E({Ex}, {Ey})$", bottom-right
vector: (Ax, Ay), (Cx, Cy), blue
vector: (Ax, Ay), (Bx, By), teal
vector: (Bx, By), (Cx, Cy), red
line: (Dx, Dy), (Bx, By), dashed, gray
text: 0.5 * (Ax + Dx) + 0.2, 0.5 * (Ay + Dy) - 0.1, "$\vec{v} = [2, -4]$", bottom-left
text: 0.5 * (Ax + Bx), 0.5 * (Ay + By), "$\vec{u}$", top-left
text: 0.5 * (Bx + Cx), 0.5 * (By + Cy), "$\vec{w}$", bottom-right
angle-arc: (Ax, Ay), 0.3, -63.43, 18.43, black, solid
text: Ax + 0.2, Ay + 0.05, "$\alpha$", bottom-right
:::



:::{plot}
width: 70%
ticks: off
axis: equal
let: Ax = -1
let: Ay = 2
let: Bx = 4
let: By = 3
let: vx = Bx - Ax
let: vy = By - Ay
let: ux = 1
let: uy = 3
let: Cx = Bx + ux
let: Cy = By + uy
let: Dx = Ax + ux
let: Dy = Ay + uy
point: (Ax, Ay)
point: (Bx, By)
point: (Cx, Cy)
point: (Dx, Dy)
text: Ax, Ay, "$A(-1, 2)$", bottom-left
text: Bx, By, "$B(4, 3)$", bottom-right
text: Cx, Cy, "$C$", top-right
text: Dx, Dy, "$D$", top-left
vector: Ax, Ay, vx, vy, blue
vector: Ax, Ay, ux, uy, red
line-segment: (Dx, Dy), (Cx, Cy), solid, black
line-segment: (Bx, By), (Cx, Cy), solid, black
text: 0.5 * (Ax + Dx), 0.5 * (Ay + Dy), "$\vec{u} = [1, 3]$", top-left
text: 0.5 * (Ax + Bx), 0.5 * (Ay + By) - 0.3, "$\vec{v}$", bottom-center
let: Ex = Ax + 40/26
let: Ey = Ay + 8/26
point: (Ex, Ey)
text: Ex, Ey, "$E$", bottom-right
line-segment: (Ex, Ey), (Dx, Dy), dashed, gray
let: p = 0.08
let: dvx = p * vx
let: dvy = p * vy
let: dvtx = -p * vy
let: dvty = p * vx
line-segment: (Ex + dvx, Ey + dvy), (Ex + dvx + dvtx, Ey + dvy + dvty), solid, teal
line-segment: (Ex + dvtx, Ey + dvty), (Ex + dvx + dvtx, Ey + dvy + dvty), solid, teal
fill-polygon: (Ex, Ey), (Ex + dvx, Ey + dvy), (Ex + dvx + dvtx, Ey + dvy + dvty), (Ex + dvtx, Ey + dvty), teal, 0.3
let: Mx = 0.5 * (Dx + Ex)
let: My = 0.5 * (Dy + Ey)
point: (Mx, My)
text: Mx, My, "$M$", top-right
:::





:::{plot}
width: 70%
axis: equal
let: x0 = 4
let: y0 = 2
let: ux = -2
let: uy = 5
let: vx = 4
let: vy = -1
vector: x0, y0, ux, uy, blue
vector: x0, y0, vx, vy, red
line-segment: (x0 + ux, y0 + uy), (x0 + vx, y0 + vy), dashed, gray
line-segment: (x0 + ux, y0 + uy), (x0 + ux + vx, y0 + uy + vy), solid, black
line-segment: (x0 + ux + vx, y0 + uy + vy), (x0 + vx, y0 + vy), solid, black
point: (x0 + ux, y0 + uy)
point: (x0 + vx, y0 + vy)
point: (x0 + ux + vx, y0 + uy + vy)
point: (x0, y0)
line-segment: (x0, y0), (x0 + ux + vx, y0 + uy + vy), dashed, gray
point: (x0 + 0.5 * (ux + vx), y0 + 0.5 * (uy + vy))
xmin: -1
xmax: 11
ymin: -1
ymax: 8
ticks: off
let: Ax = x0
let: Ay = y0
let: Dx = x0 + ux
let: Dy = y0 + uy
let: Bx = x0 + vx
let: By = y0 + vy
let: Cx = x0 + ux + vx
let: Cy = y0 + uy + vy
let: Mx = x0 + 0.5 * (ux + vx)
let: My = y0 + 0.5 * (uy + vy)
text: Ax - 0.1, Ay, "$A({x0}, {y0})$", bottom-left
text: Bx + 0.1, By, "$B$", bottom-right
text: Cx + 0.1, Cy, "$C$", top-right
text: Dx - 0.1, Dy, "$D({Dx}, {Dy})$", top-left
text: Mx + 0.2, My, "$M$", center-right
text: 0.5 * (Ax + Bx), 0.5 * (Ay + By) - 0.4, "$\vec{a} = [4, -1]$", bottom-center
text: 0.5 * (Ax + Dx) - 0.4, 0.5 * (Ay + Dy), "$\vec{b}$", bottom-left
let: Px = 10
let: Py = 4
point: (Px, Py)
text: Px + 0.1, Py, "$P({Px}, {Py})$", top-right
let: nx = -(Cy - By)
let: ny = Cx - Bx
let: n_length = (nx**2 + ny**2)**0.5
let: h_n_dot = (Px - Bx) * nx + (Py - By) * ny
let: hx = h_n_dot / n_length**2 * nx 
let: hy = h_n_dot / n_length**2 * ny
let: Rx = Px - hx
let: Ry = Py - hy
line-segment: (Px, Py), (Rx, Ry), dashed, gray
point: (Rx, Ry)
text: Rx, Ry + 0.2, "$R$", top-right
line-segment: (Cx, Cy), (Px, Py), dashdot, gray
line-segment: (Bx, By), (Px, Py), dashdot, gray
fill-polygon: (Bx, By), (Cx, Cy), (Px, Py), blue, 0.2
let: p = 0.08
let: BC_x = Cx - Bx
let: BC_y = Cy - By
let: drx = -p * BC_x
let: dry = -p * BC_y
let: drtx = p * BC_y
let: drty = -p * BC_x
line-segment: (Rx + drx, Ry + dry), (Rx + drx + drtx, Ry + dry + drty), solid, teal
line-segment: (Rx + drtx, Ry + drty), (Rx + drx + drtx, Ry + dry + drty), solid, teal
:::




Renders a static mathematical figure from key-value primitives.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `width` | length / percentage |
| `align` | value |
| `class` | CSS class list |
| `name` | string |
| `nocache` | flag |
| `debug` | flag |
| `alt` | string |
| `usetex` | string |
| `xmin` | string |
| `xmax` | string |
| `ymin` | string |
| `ymax` | string |
| `xstep` | string |
| `ystep` | string |
| `fontsize` | string |
| `ticks` | string |
| `grid` | string |
| `xticks` | string |
| `yticks` | string |
| `lw` | string |
| `alpha` | string |
| `figsize` | string |
| `endpoint_markers` | string |
| `function-endpoints` | string |
| `xlabel` | string |
| `ylabel` | string |

## Example

````markdown
:::{plot}
function: x**2 - 1, f
point: (1, f(1))
xmin: -3
xmax: 3
ymin: -2
ymax: 5
grid: on
:::
````

## Notes

- Supports many primitives: `function`, `point`, `line`, `line-segment`, `polygon`, `vector`, `circle`, `ellipse`, `curve`, `text`, `annotate`, and more.

## Source

`src/munchboka_edutools/directives/plot.py`
