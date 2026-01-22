# Animate Directive Examples

The `animate` directive extends the `plot` directive to create animations by varying one or more variables across frames.

## Basic Function Animation

Here's a simple animation of a sine wave with varying frequency:

:::{animate}
animate-var: a, 1, 5, 20
fps: 10
function: sin(a*x)
xmin: -10
xmax: 10
ymin: -2
ymax: 2
grid: true
width: 80%
:::
Sinusfunksjon med varierende frekvens $a$ fra 1 til 5.

## Rotating Vector

Animate a vector rotating around the origin:

:::{animate}
animate-var: theta, 0, 360, 36
fps: 12
vector: 0, 0, 3*cos(theta*pi/180), 3*sin(theta*pi/180), blue
point: 0, 0
xmin: -4
xmax: 4
ymin: -4
ymax: 4
grid: true
ticks: true
width: 70%
:::
En vektor som roterer $360°$ rundt origo.

## Moving Point on Parabola

Animate a point moving along a parabola:

:::{animate}
animate-var: t, -5, 5, 40
fps: 15
function: x**2, f
point: t, t**2
annotate: (t, t**2), (t, -2), f"$(t, t^2)$", 0.3
xmin: -6
xmax: 6
ymin: -2
ymax: 26
grid: true
width: 75%
:::
Et punkt beveger seg langs parabelen $f(x) = x^2$.

## Wave Interference

Two waves with phase difference:

:::{animate}
animate-var: phi, 0, 2*pi, 30
fps: 10
function: sin(x), "Bølge 1"
function: sin(x + phi), "Bølge 2"
function: sin(x) + sin(x + phi), "Sum"
xmin: -10
xmax: 10
ymin: -3
ymax: 3
grid: true
fontsize: 18
width: 85%
:::
Interferens mellom to bølger med faseforskjell $\phi$.

## Expanding Circle

A circle that grows in radius:

:::{animate}
animate-var: r, 0.5, 4, 25
fps: 8
circle: 0, 0, r, solid, blue
point: 0, 0
xmin: -5
xmax: 5
ymin: -5
ymax: 5
axis: equal
grid: true
width: 70%
:::
En sirkel som vokser fra radius $0.5$ til $4$.

## Tangent Line Animation

A tangent line moving along a curve:

:::{animate}
animate-var: a, -4, 4, 40
fps: 12
function: x**3 - 3*x, f
point: a, a**3 - 3*a
line: 3*a**2 - 3, (a**3 - 3*a) - a*(3*a**2 - 3), solid, red
xmin: -5
xmax: 5
ymin: -10
ymax: 10
grid: true
width: 80%
:::
Tangentlinje til $f(x) = x^3 - 3x$ i punktet $(a, f(a))$.

## Options Reference

### Animation-Specific Options

- `animate-var: name, start, end, frames` - Define animation variable
  - `name`: Variable identifier (must be valid Python identifier)
  - `start`: Starting value (supports SymPy expressions like `pi`, `sqrt(2)`)
  - `end`: Ending value (supports SymPy expressions)
  - `frames`: Number of frames (positive integer)

- `fps: 10` - Frames per second (default: 10)

- `duration: 200` - Frame duration in milliseconds (alternative to fps)

- `loop: true` - Loop animation infinitely (default: true)

- `format: webp` - Output format: `webp` (default) or `gif`

### All Plot Options Work

The animate directive supports all options from the plot directive:

- `function`, `point`, `vector`, `circle`, `ellipse`, `curve`
- `line`, `line-segment`, `vline`, `hline`, `polygon`
- `annotate`, `text`, `bar`, `angle-arc`
- `xmin`, `xmax`, `ymin`, `ymax`, `xstep`, `ystep`
- `grid`, `ticks`, `xlabel`, `ylabel`, `fontsize`
- `width`, `align`, `class`, `alt`, `name`

## Tips and Best Practices

### Performance

- Keep frame count reasonable (20-50 frames is usually sufficient)
- Use WebP format for smaller file sizes and better quality
- Cache is automatic - animations regenerate only when content changes

### Variable Substitution

The animation variable can appear anywhere in plot content:

```markdown
:::{animate}
animate-var: n, 1, 10, 10
function: x**n
point: 1, 1**n
:::
```

Variables support mathematical expressions:
- `animate-var: t, 0, 2*pi, 30`
- `animate-var: a, -sqrt(5), sqrt(5), 20`
- `animate-var: n, 1, E, 15`

### Combining with Multi-Plot

Animations work inside `multi-plot2` containers:

:::::{multi-plot2}
rows: 1
cols: 2

:::{animate}
animate-var: a, 1, 5, 20
function: sin(a*x)
xmin: -10
xmax: 10
:::

:::{animate}
animate-var: a, 1, 5, 20
function: cos(a*x)
xmin: -10
xmax: 10
:::
:::::

### File Sizes

- WebP typically produces 30-50% smaller files than GIF
- Higher FPS = smoother animation but larger file
- More frames = longer animation and larger file
- Reduce `fontsize` and `lw` for smaller output

### Browser Compatibility

- WebP: Modern browsers (Chrome, Firefox, Edge, Safari 14+)
- GIF: Universal compatibility
- Both formats support transparency
