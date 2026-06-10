# `plot3d` — 3D vector geometry figures

The `plot3d` directive renders three-dimensional figures using an oblique/axonometric
projection. All 3D objects are projected to a 2D plane and drawn with standard
Matplotlib artists, so the output is a clean inline SVG — just like `plot`.

## Projection parameters

| Key | Default | Description |
|-----|---------|-------------|
| `azimuth` | `40` | Rotation of the x/y plane in degrees |
| `elevation` | `25` | Tilt of the z-axis in degrees |

## Axis bounds

Use a single number for symmetric bounds or a `(lo, hi)` pair:

```
xrange: 5        # → (−5, 5)
yrange: (-2, 8)  # → (−2, 8)
```

## Example 1 — coordinate system only

:::{plot3d}
xrange: 5
yrange: 5
zrange: (0, 5)
:::

## Example 2 — vectors

:::{plot3d}
xrange: 5
yrange: 5
zrange: (0, 5)
vector: (0,0,0), (3,1,0), blue
vector: (0,0,0), (0,2,3), red
vector: (0,0,0), (3,3,3), green
:::

## Example 3 — points and line segment

:::{plot3d}
xrange: 5
yrange: 5
zrange: (0, 5)
point: (2, 1, 3), blue
point: (-1, 3, 1), red
line-segment: (2,1,3), (-1,3,1), dashed, gray
:::

## Example 4 — plane

:::{plot3d}
xrange: 5
yrange: 5
zrange: (0, 5)
grid-planes: xy
plane: normal=(0,0,1), through=(0,0,2), color=blue, alpha=0.15
:::

## Example 5 — sphere

:::{plot3d}
xrange: 5
yrange: 5
zrange: 5
sphere: (0,3,0), 3, blue
:::


:::{plot3d}
xrange: 5
yrange: 5
zrange: 5
sphere: (2,3,4), 1, blue
:::

:::{plot3d}
xrange: 5
yrange: 5
zrange: 5
sphere: (-2,3,4), 1, blue
sphere: (-2,-3,4), 1, teal
sphere: (-2,-3,-4), 1, purple
sphere: (2,-3,-4), 1, red
:::

## Example 6 — angle between two vectors

:::{plot3d}
xrange: 5
yrange: 5
zrange: (0, 5)
vector: (0,0,0), (3,0,0), blue
vector: (0,0,0), (0,3,0), red
angle: (0,0,0), (1,0,0), (0,1,0), 1.2, purple
:::

## Example 7 — parametric curve

:::{plot3d}
xrange: 5
yrange: 5
zrange: (0, 7)
curve: cos(3*t), 2*sin(4*t), t, (0, 6.28), blue
:::

## Example 8 — pyramid

:::{plot3d}
xrange: 5
yrange: 5
zrange: (0, 5)
pyramid: apex=(0,0,4), base=((2,2,0),(-2,2,0),(-2,-2,0),(2,-2,0)), color=blue, alpha=0.2
:::

:::{plot3d}
xrange: 5
yrange: 5
zrange: (0, 6)
pyramid: apex=(0,0,5), base=((0,0,0),(5,0,0),(4,2,0)), color=blue, alpha=0.2
ticks: off
:::



## Example 9 — full scene

:::{plot3d}
azimuth: 35
elevation: 55
xrange: 6
yrange: 6
zrange: (0, 6)
grid-planes: xy
vector: (0,0,0), (4,0,0), blue
vector: (0,0,0), (0,4,0), red
vector: (0,0,0), (0,0,4), green
point: (4, 4, 4), purple
line-segment: (0,0,0), (4,4,4), dashed, gray
angle: (0,0,0), (1,0,0), (0,1,0), 1.0, orange
:::

## Example 10 — right-angle markers

:::{plot3d}
xrange: 5
yrange: 5
zrange: (0, 5)
vector: (0,0,0), (3,0,0), blue
vector: (0,0,0), (0,3,0), red
vector: (0,0,0), (0,0,3), green
right-angle: (0,0,0), (1,0,0), (0,1,0), 0.4, gray
right-angle: (0,0,0), (1,0,0), (0,0,1), 0.4, gray
right-angle: (0,0,0), (0,1,0), (0,0,1), 0.4, gray
:::

## Example 11 — projections

Point projected onto xy, xz, and yz planes with drop lines:

:::{plot3d}
xrange: 5
yrange: 5
zrange: (0, 5)
point: (3,3,3), blue
projection: object=point:(3,3,3), onto=xy, color=blue, alpha=0.4, drop=true
projection: object=point:(3,3,3), onto=xz, color=red,  alpha=0.4, drop=true
projection: object=point:(3,3,3), onto=yz, color=green, alpha=0.4, drop=true
:::

Sphere projected onto xy-plane:

:::{plot3d}
xrange: 5
yrange: 5
zrange: (0, 5)
sphere: (3,3,3), 1, red
projection: object=sphere:(3,3,3),1, onto=yz, color=red, alpha=0.25, drop=true
:::

## Example 12 — symmetric layout

The same scene rendered with `layout: symmetric` — both the x- and y-axes
appear at ±45° below horizontal, giving a more balanced isometric look.

:::{plot3d}
layout: symmetric
elevation: 30
xrange: 5
yrange: 5
zrange: (0, 5)
vector: (0,0,0), (3,0,0), blue
vector: (0,0,0), (0,3,0), red
vector: (0,0,0), (0,0,3), green
:::

:::{plot3d}
layout: symmetric
elevation: 30
xrange: 5
yrange: 5
zrange: (0, 5)
point: (3,2,3), blue
sphere: (1,1,1), 1.2, red
line-segment: (0,0,0),(3,2,3), blue
:::

## Example 13 — solid of revolution (disk method)

Rotating $f(x) = \sqrt{x}$ around the x-axis for $x \in [0, 4]$:

:::{plot3d}
xrange: (0, 4.5)
yrange: (-2.5, 2.5)
zrange: (-2.5, 2.5)
ticks: false
xlabel: $x$
ylabel: $y$
zlabel: $z$
solid-of-revolution: sqrt(x), (0, 4), blue, alpha=0.35, disks=4
:::

The same solid in symmetric layout:

:::{plot3d}
layout: symmetric
elevation: 30
xrange: (0, 4.5)
yrange: (-2.5, 2.5)
zrange: (-2.5, 2.5)
ticks: false
xlabel: $x$
ylabel: $y$
zlabel: $z$
solid-of-revolution: sqrt(x), (0, 4), blue, alpha=0.35, disks=4
:::

## Example 14 — limited plane

A rectangular patch of the plane $z = x + y$ over $x \in [0,3],\; y \in [0,2]$:

:::{plot3d}
xrange: (0, 4)
yrange: (0, 3)
zrange: (0, 6)
xlabel: $x$
ylabel: $y$
zlabel: $z$
limited-plane: z = x + y, (0, 3), (0, 2), blue, alpha=0.3
vector: (0,0,0), (3,0,0), blue
vector: (0,0,0), (0,2,0), red
vector: (0,0,0), (0,0,5), green
:::

A horizontal plane $z = 2$ and a vertical plane $y = 1$ together:

:::{plot3d}
xrange: (0, 4)
yrange: (0, 4)
zrange: (0, 4)
xlabel: $x$
ylabel: $y$
zlabel: $z$
limited-plane: z = 2, (0, 3), (0, 3), blue, alpha=0.25
limited-plane: y = 1, (0, 3), (0, 3), red, alpha=0.25
:::

The same scene in symmetric layout:

:::{plot3d}
layout: symmetric
elevation: 30
xrange: (0, 4)
yrange: (0, 4)
zrange: (0, 4)
xlabel: $x$
ylabel: $y$
zlabel: $z$
limited-plane: z = 2, (0, 3), (0, 3), blue, alpha=0.25
limited-plane: y = 1, (0, 3), (0, 3), red, alpha=0.25
:::
