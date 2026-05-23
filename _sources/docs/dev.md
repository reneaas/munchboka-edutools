# Dev


:::{plot}
width: 70%
axis: off
axis: equal
let: r = 4
circle: (0, 0), r, blue, solid
let: N = 8
let: M = 11
repeat: n=0..M; line-segment: (r * cos(4 * n * pi / M), r * sin(4 * n * pi / M)), (r * cos(4 * (n + 1) * pi / M), r * sin(4 * (n + 1) * pi / M)), solid, black
let: Ax = r
let: Ay = 0
let: Bx = r * cos(120 * pi / 180)
let: By = r * sin(120 * pi / 180)
:::



:::{plot}
width: 70%
axis: off
axis: equal
let: r = 4
circle: (0, 0), r, blue, solid
let: N = 6
let: M = 2 * N
repeat: n=0..N; line-segment: (r * cos(4 * n * pi / N), r * sin(4 * n * pi / N)), (r * cos(4 * (n + 1) * pi / N), r * sin(4 * (n + 1) * pi / N)), dashed, black
repeat: n=0..M; line-segment: (r * cos(4 * n * pi / M), r * sin(4 * n * pi / M)), (r * cos(4 * (n + 1) * pi / M), r * sin(4 * (n + 1) * pi / M)), solid, black
let: Ax = r
let: Ay = 0
let: Bx = r * cos(120 * pi / 180)
let: By = r * sin(120 * pi / 180)
text: 0.5 * (Ax + Bx), 0.5 * (Ay + By), "$3$", bottom-left
:::


:::{plot}
width: 70%
lw: 1.5
axis: equal
ticks: off
circle: (0, 0), 1, blue
let: u = 240
angle-arc: (0, 0), 0.2, 0, u
let: Px = cos(u * pi/180)
let: Py = sin(u * pi/180)
line-segment: (0, 0), (Px, Py), solid, red
line-segment: (Px, Py), (0, Py), dashed, red
let: ds = 0.1
line-segment: (0, Py + ds), (-ds, Py + ds), solid, gray
line-segment: (-ds, Py + ds), (-ds, Py), solid, gray
text: -0.25, 0.2, "$240^\circ$", center-center
point: (Px, Py)
text: Px, Py, "$P(x, y)$", bottom-left
text: 0.5 * Px, 0.5 * Py, "$1$", top-left
:::



:::{plot}
width: 70%
lw: 1.5
axis: off
axis: equal
let: Ax = 0
let: Ay = 0
let: u = 45
let: Cx = 8 * cos(u * pi/180)
let: Cy = 8 * sin(u * pi/180)
let: Bx = 4
let: By = 0
let: v = 105
let: Dx = 6 * cos((u + v) * pi/180)
let: Dy = 6 * sin((u + v) * pi/180)
line-segment: (Ax, Ay), (Bx, By), solid, black
line-segment: (Ax, Ay), (Cx, Cy), dashed, black
line-segment: (Ax, Ay), (Dx, Dy), solid, black
line-segment: (Bx, By), (Cx, Cy), solid, black
line-segment: (Cx, Cy), (Dx, Dy), solid, black
text: Ax, Ay, "$A$", bottom-left
text: Bx, By, "$B$", bottom-right
text: Cx, Cy, "$C$", top-right
text: Dx, Dy, "$D$", center-left
text: 0.5 * (Ax + Cx), 0.5 * (Ay + Cy), "$8$", top-left
angle-arc: (Ax, Ay), 1.3, 0, u
text: 2 * 0.5 * (cos(u * pi/180) + 1), 2 * 0.5 * sin(u * pi/180), "$45^\circ$", center-center
text: 0.5 * (Ax + Bx), 0.5 * (Ay + By) - 0.4, "$4$", bottom-center
let: r = 1.1
angle-arc: (Ax, Ay), r, u, u + v
text: 0, r * 1.2, "$105^\circ$", center-center
let: DA = sqrt((Dx - Ax) ** 2 + (Dy - Ay) ** 2)
let: DC = sqrt((Dx - Cx) ** 2 + (Dy - Cy) ** 2)
let: DA_x = Ax - Dx
let: DA_y = Ay - Dy
let: DC_x = Cx - Dx
let: DC_y = Cy - Dy
let: dot_product = DA_x * DC_x + DA_y * DC_y
let: angle_rad = acos(dot_product / (DA * DC))
let: angle_deg = angle_rad * 180 / pi
angle-arc: (Dx, Dy), r, u + v + 180, u + v + 180 + angle_deg
text: Dx + 1.9*r * cos((u + v + 180 + angle_deg / 2) * pi/180), Dy + r * sin((u + v + 180 + angle_deg / 2) * pi/180), "${angle_deg:.2f}^\circ$", center-center
:::
