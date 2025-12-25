# `plot` directive

The plot directive allows you to create figures using a simple markup syntax. Below are some examples demonstrating its usage.

## Full Keyword Specification

### Global Figure Options

| Keyword | Type | Default | Description |
|---------|------|---------|-------------|
| `width` | string | - | CSS width as percentage (e.g., `100%`) or pixels (e.g., `400px`) |
| `figsize` | tuple | auto | Figure size in inches: `(width, height)` |
| `align` | string | `center` | Figure alignment: `left`, `center`, or `right` |
| `class` | string | - | Extra CSS classes for the figure container |
| `name` | string | auto | Stable output filename / anchor for cache |
| `alt` | string | auto | Alt text for accessibility |
| `nocache` | bool | false | Force regeneration (bypass cache) |
| `debug` | bool | false | Keep raw SVG size & emit debug info |

### Axis Configuration

| Keyword | Type | Default | Description |
|---------|------|---------|-------------|
| `xmin` | float/expr | -6 | Minimum x-axis value (accepts SymPy expressions) |
| `xmax` | float/expr | 6 | Maximum x-axis value (accepts SymPy expressions) |
| `ymin` | float/expr | -6 | Minimum y-axis value (accepts SymPy expressions) |
| `ymax` | float/expr | 6 | Maximum y-axis value (accepts SymPy expressions) |
| `xstep` | float/expr | 1 | Spacing between x-axis ticks |
| `ystep` | float/expr | 1 | Spacing between y-axis ticks |
| `xlabel` | string | - | X-axis label (LaTeX supported); can add padding: `$x$, 8` |
| `ylabel` | string | - | Y-axis label (LaTeX supported); can add padding: `$y$, 8` |
| `axis` | string | - | Special modes: `off` (hide axes), `equal` (1:1 aspect), `tight` |
| `ticks` | bool | true | Master toggle for ticks/labels (`true`/`false` or `on`/`off`) |
| `xticks` | string | - | Set to `off` to hide x-axis ticks |
| `yticks` | string | - | Set to `off` to hide y-axis ticks |

### Appearance Options

| Keyword | Type | Default | Description |
|---------|------|---------|-------------|
| `fontsize` | float | 20 | Base font size for labels and ticks |
| `lw` | float | 2.5 | Default line width for function curves |
| `alpha` | float | 1.0 | Global transparency for function/curve lines (0.0-1.0) |
| `grid` | bool | false | Toggle grid lines (`true`/`false` or `on`/`off`) |
| `usetex` | bool | true | Use LaTeX text rendering via matplotlib |

### Plotting Primitives (Repeatable)

#### Functions

| Syntax | Description |
|--------|-------------|
| `function: expr` | Plot function with `x` as variable |
| `function: expr, label` | Plot with custom label |
| `function: expr, (a, b)` | Plot with domain restriction |
| `function: expr, (a, b) \ {x1, x2}` | Plot with domain exclusions |
| `function: expr, label, (a, b), color` | Full specification with all options |

**Examples:**
- `function: x**2 - 3*x + 2, f`
- `function: sin(x)/x, (-6*pi, 6*pi) \ {0}`
- `function: x**2 * exp(-x), g, (0, 10), red`

#### Geometric Elements

| Keyword | Syntax | Description |
|---------|--------|-------------|
| `point` | `(x, y)` | Mark a point; supports expressions and function calls like `f(2)` |
| `vline` | `x [, ymin, ymax] [, style] [, color]` | Vertical line at x |
| `hline` | `y [, xmin, xmax] [, style] [, color]` | Horizontal line at y |
| `line` | `a, (x0, y0) [, style] [, color]` | Line through point with slope: y = a*(x-x0) + y0 |
| `line` | `a, b [, style] [, color]` | Line with slope-intercept: y = ax + b |
| `line` | `(x1, y1), (x2, y2) [, style] [, color]` | Line through two points (infinite extent) |
| `tangent` | `x0, f [, style] [, color]` or `(x0, f(x0)) [, style] [, color]` | Tangent to a previously defined function label at `x0` |
| `line-segment` | `(x1, y1), (x2, y2) [, style] [, color]` | Finite line segment |
| `polygon` | `(x1, y1), (x2, y2), ... [, show_vertices]` | Polygon outline |
| `fill-polygon` | `(x1, y1), (x2, y2), ... [, color] [, alpha]` | Filled polygon (default alpha 0.1) |
| `bar` | `(x, y), length, orientation` | Dimension bar (orientation: `horizontal`/`vertical`) |
| `vector` | `x, y, dx, dy [, color]` | Arrow vector from (x,y) with components (dx,dy) |

#### Advanced Shapes

| Keyword | Syntax | Description |
|---------|--------|-------------|
| `circle` | `(cx, cy), radius [, style] [, color]` | Circle with center and radius |
| `ellipse` | `(cx, cy), a, b [, style] [, color]` | Ellipse with center and semi-axes a, b |
| `curve` | `x_expr, y_expr, (t0, t1) [, style] [, color]` | Parametric curve with parameter `t` |
| `angle-arc` | `(cx, cy), radius, start_deg, end_deg [, style] [, color]` | Arc showing angle (degrees, CCW) |

#### Annotations & Text

| Keyword | Syntax | Description |
|---------|--------|-------------|
| `annotate` | `(xytext), (xy), "text" [, arc]` | Arrow annotation with optional arc curvature |
| `text` | `x, y, "string" [, pos] [, bbox]` | Text at position with optional alignment |

**Text positions:** `top-left`, `top-center`, `top-right`, `center-left`, `center-center`, `center-right`, `bottom-left`, `bottom-center`, `bottom-right`. Add `long` prefix for more offset (e.g., `longtop-left`).

### Style Options

**Line styles:** `solid`, `dashed`, `dotted`, `dashdot`

**Colors:** Can use:
- Named colors from `plotmath.COLORS` palette
- Matplotlib named colors (e.g., `red`, `blue`, `green`)
- Hex colors (e.g., `#FF5733`)
- Common palette names: `teal`, `orange`, `purple`, `gray`

### Expression Support

Almost all numeric fields accept **SymPy expressions**:
- Mathematical constants: `pi`, `E` (Euler's number)
- Functions: `sqrt`, `exp`, `log`, `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `Abs`
- Arithmetic: `+`, `-`, `*`, `/`, `**` (power)
- Examples: `2*sqrt(5)`, `exp(1/3)`, `pi/4`, `3*cos(pi/6)`

**Function label calls:** Use `f(x)` syntax in points to evaluate a plotted function:
- `point: (2, f(2))` - plot point at x=2, y=f(2)
- Works with any function label defined in `function:` directive

**Tangents:** Use `tangent:` to draw the tangent line to a labeled function at a given x-value:
- Preferred simple form: `tangent: x0, f [, style] [, color]`, e.g. `tangent: 1, f, dashed, red`.
- Legacy form (still supported): `tangent: (x0, f(x0)) [, style] [, color]`.
- In both forms, `x0` can be an expression like `2 - sqrt(2)`.
- Optional style and color work like for `line`/`vline`/`hline`.
- If no style/color is given, tangents default to a dashed orange line.

### Usage Notes

- **Multiple values**: Keywords like `function`, `point`, `vline`, `hline`, etc. can be repeated
- **Order independence**: For primitives with optional style/color, order doesn't matter after required numeric parts
- **Discontinuities**: Use domain exclusions with `\ {x1, x2}` to handle function discontinuities
- **Caption**: Any content after a blank line becomes the figure caption
- **Caching**: Plots are cached based on content hash; use `nocache: true` to force regeneration

---

## Examples

### Example 1

Code:

````markdown
:::{plot}
width: 70%
function: x**2 - 3*x + 2, f
:::
````

Output:

:::{plot}
width: 70%
function: x**2 - 3*x + 2, f
:::


### Example 2

Code:

```markdown
:::{plot}
width: 70%
function: x ** 2 * exp(-x), g, (0, 10), red
xmin: -1
xmax: 11
ymax: 1
ymin: -0.1
yticks: off
grid: off
:::
```

Output:

:::{plot}
width: 70%
function: x ** 2 * exp(-x), g, (0, 10), red
xmin: -1
xmax: 11
ymax: 1
ymin: -0.1
yticks: off
grid: off
:::



### Example 3

Code:

````markdown
:::{plot}
width: 60%
axis: off
polygon: (0, 0), (44, 0), (44, 20), (0, 20)
xmin: -5
xmax: 45
ymax: 22
ymin: -2
text: 22, 0, "$x$", bottom-center
text: 44, 10, "$y$", center-right
figsize: (4, 2)
:::
````

Output:

:::{plot}
width: 50%
axis: off
polygon: (0, 0), (44, 0), (44, 20), (0, 20)
xmin: -5
xmax: 45
ymax: 22
ymin: -2
text: 22, 0, "$x$", bottom-center
text: 44, 10, "$y$", center-right
figsize: (4, 2)
:::


### Example 4


Code: 

````markdown
:::{plot}
width: 70%
axis: off
figsize: (5, 3)
hline: 0, -10, 10, solid, blue
line-segment: (0, 0), (8, 0), black, solid
line-segment: (-4, 0), (-4, 5), black, solid
line-segment: (-4, 5), (4, 5), black, solid
line-segment: (4, 5), (4, 0), black, solid
text: 0, 0, "River", bottom-center
annotate: (5, 5), (0, 5), "Fence", 0.5
:::
````

Output:

:::{plot}
width: 70%
axis: off
figsize: (5, 3)
hline: 0, -10, 10, solid, blue
line-segment: (0, 0), (8, 0), black, solid
line-segment: (-4, 0), (-4, 5), black, solid
line-segment: (-4, 5), (4, 5), black, solid
line-segment: (4, 5), (4, 0), black, solid
text: 0, 0, "River", bottom-center
annotate: (5, 5), (0, 5), "Fence", 0.5
:::


### Example 5

Code: 

```markdown
:::{plot}
width: 70%
function: 8/(x**2 + 20), (0, 20), f
xmin: -1
xmax: 15
ymin: -0.1
ymax: 0.5
ystep: 0.1
point: (5, f(5))
point: (0, 0)
point: (0, f(5))
point: (5, 0)
polygon: (0, 0), (5, 0), (5, f(5)), (0, f(5))
text: 0, 0, "$(0, 0)$", bottom-left
text: 5, 0, "$(r, 0)$", bottom-center
text: 5, f(5), "$(r, f(r))$", top-right
text: 0, f(5), "$(0, f(r))$", top-left
ticks: off
:::
```

Output:

:::{plot}
width: 70%
function: 8/(x**2 + 20), (0, 20), f
xmin: -1
xmax: 15
ymin: -0.1
ymax: 0.5
ystep: 0.1
point: (5, f(5))
point: (0, 0)
point: (0, f(5))
point: (5, 0)
polygon: (0, 0), (5, 0), (5, f(5)), (0, f(5))
text: 0, 0, "$(0, 0)$", bottom-left
text: 5, 0, "$(r, 0)$", bottom-center
text: 5, f(5), "$(r, f(r))$", top-right
text: 0, f(5), "$(0, f(r))$", top-left
ticks: off
:::


### Example 6

```markdown
:::{plot}
width: 70%
axis: off
xmin: -1
xmax: 10
ymax: 5
ymin: -2
hline: 0, -1, 10, solid
vline: 0, 0, 2, dashed, gray
vline: 9, 0, 4, dashed, gray
point: (0, 2)
point: (4, 0)
point: (9, 4)
line-segment: (0, 2), (4, 0), black, solid
line-segment: (4, 0), (9, 4), black, solid
vline: 0.65, 0, 0.4, solid, black
hline: 0.4, 0, 0.65, solid, black
vline: 8.35, 0, 0.4, solid, black
hline: 0.4, 9, 8.35, solid, black
text: 4, 0, "$B$", top-center
text: 0, 2, "$A$", top-left
text: 9, 4, "$C$", top-right
lw: 1.5
point: (0, 0)
text: 0, -0.2, "$S$", bottom-left
bar: (0, -0.3), 4, horizontal
text: 2, -0.3, "$x$ km", bottom-center
bar: (0, -0.8), 9, horizontal
text: 4.5, -0.8, "9 km", bottom-center
bar: (-0.5, 0), 2, vertical
text: -0.5, 1, "2 km", center-left
bar: (9.5, 0), 4, vertical
text: 9.5, 2, "4 km", center-right
:::
```


Output:

:::{plot}
width: 70%
axis: off
xmin: -1
xmax: 10
ymax: 5
ymin: -2
hline: 0, -1, 10, solid
vline: 0, 0, 2, dashed, gray
vline: 9, 0, 4, dashed, gray
point: (0, 2)
point: (4, 0)
point: (9, 4)
line-segment: (0, 2), (4, 0), black, solid
line-segment: (4, 0), (9, 4), black, solid
vline: 0.65, 0, 0.4, solid, black
hline: 0.4, 0, 0.65, solid, black
vline: 8.35, 0, 0.4, solid, black
hline: 0.4, 9, 8.35, solid, black
text: 4, 0, "$B$", top-center
text: 0, 2, "$A$", top-left
text: 9, 4, "$C$", top-right
lw: 1.5
point: (0, 0)
text: 0, -0.2, "$S$", bottom-left
bar: (0, -0.3), 4, horizontal
text: 2, -0.3, "$x$ km", bottom-center
bar: (0, -0.8), 9, horizontal
text: 4.5, -0.8, "9 km", bottom-center
bar: (-0.5, 0), 2, vertical
text: -0.5, 1, "2 km", center-left
bar: (9.5, 0), 4, vertical
text: 9.5, 2, "4 km", center-right
:::


### Example 7

:::{plot}
width: 80%
align: right
ticks: off
axis: off
xmin: -20
xmax: 160
ymax: 80
ymin: -1
lw: 1.5
figsize: (3, 3)
function: 70/75**2 * (x - 75)**2, (0, 150), blue
hline: 70, 0, 150, solid, blue
hline: 0, 0, 75, dashed, gray
bar: (-10, 0), 70, vertical
text: -10, 35, "70 cm", center-left
bar: (0, 75), 150, horizontal
text: 75, 75, "150 cm", top-center
:::

A figure may be right-aligned by specifying `align: right`. 

Let's say we want to showcase a smaller piece of a figure while simultaneously providing a larger context as well. 


:::{clear}
:::

Then we may create the full figure as below:

:::{plot}
width: 80%
ticks: off
axis: off
xmin: -20
xmax: 500
ymax: 100
ymin: -100
lw: 1
figsize: (7, 5)
function: 70/75**2 * (x - 75)**2, (0, 150), blue
function: -70/75**2 * (x - (75 * sqrt(2) + 75))**2 + 70, (75 * sqrt(2), 75 * sqrt(2) + 150), blue
function: 70/75**2 * (x - (2 * 75 * sqrt(2) + 75))**2, (2 * 75 * sqrt(2), 2 * 75 * sqrt(2) + 150), blue
function: -70/75**2 * (x - (3 * 75 * sqrt(2) + 75))**2 + 70, (3 * 75 * sqrt(2), 3 * 75 * sqrt(2) + 150), blue
function: -70/75**2 * (x - 75)**2, (0, 150), blue
function: 70/75**2 * (x - (75 * sqrt(2) + 75))**2 - 70, (75 * sqrt(2), 75 * sqrt(2) + 150), blue
function: -70/75**2 * (x - (2 * 75 * sqrt(2) + 75))**2, (2 * 75 * sqrt(2), 2 * 75 * sqrt(2) + 150), blue
function: 70/75**2 * (x - (3 * 75 * sqrt(2) + 75))**2 - 70, (3 * 75 * sqrt(2), 3 * 75 * sqrt(2) + 150), blue
vline: 0, -70, 70, solid, blue
hline: -70, 0, 3 * 75 * sqrt(2) + 150, solid, blue
vline: 3 * 75 * sqrt(2) + 150, -70, 70, solid, blue
hline: 70, 0, 3 * 75 * sqrt(2) + 150, solid, blue
hline: 0, 75 * sqrt(2), 75 * sqrt(2) + 150, solid, blue
hline: 0, 3 * 75 * sqrt(2), 3 * 75 * sqrt(2) + 150, solid, blue
hline: 35, 0, 3 * 75 * sqrt(2) + 150, dashed, gray
hline: 0, 0, 3 * 75 * sqrt(2) + 150, dashed, gray
bar: (0, 80), 150, horizontal
text: 75, 85, "150 cm", top-center
bar: (-12, 35), 35, vertical 
text: -12, 52.5, "35 cm", center-left
bar: (480, 0), 70, vertical
text: 480, 35, "70 cm", center-right
:::


The source code would be this for the right-aligned figure:

```markdown
:::{plot}
width: 80%
align: right
ticks: off
axis: off
xmin: -20
xmax: 160
ymax: 80
ymin: -1
lw: 1.5
figsize: (3, 3)
function: 70/75**2 * (x - 75)**2, (0, 150), blue
hline: 70, 0, 150, solid, blue
hline: 0, 0, 75, dashed, gray
bar: (-10, 0), 70, vertical
text: -10, 35, "70 cm", center-left
bar: (0, 75), 150, horizontal
text: 75, 75, "150 cm", top-center
:::
```

And for the full figure:

```markdown
:::{plot}
width: 80%
ticks: off
axis: off
xmin: -20
xmax: 500
ymax: 100
ymin: -100
lw: 1
figsize: (7, 5)
function: 70/75**2 * (x - 75)**2, (0, 150), blue
function: -70/75**2 * (x - (75 * sqrt(2) + 75))**2 + 70, (75 * sqrt(2), 75 * sqrt(2) + 150), blue
function: 70/75**2 * (x - (2 * 75 * sqrt(2) + 75))**2, (2 * 75 * sqrt(2), 2 * 75 * sqrt(2) + 150), blue
function: -70/75**2 * (x - (3 * 75 * sqrt(2) + 75))**2 + 70, (3 * 75 * sqrt(2), 3 * 75 * sqrt(2) + 150), blue
function: -70/75**2 * (x - 75)**2, (0, 150), blue
function: 70/75**2 * (x - (75 * sqrt(2) + 75))**2 - 70, (75 * sqrt(2), 75 * sqrt(2) + 150), blue
function: -70/75**2 * (x - (2 * 75 * sqrt(2) + 75))**2, (2 * 75 * sqrt(2), 2 * 75 * sqrt(2) + 150), blue
function: 70/75**2 * (x - (3 * 75 * sqrt(2) + 75))**2 - 70, (3 * 75 * sqrt(2), 3 * 75 * sqrt(2) + 150), blue
vline: 0, -70, 70, solid, blue
hline: -70, 0, 3 * 75 * sqrt(2) + 150, solid, blue
vline: 3 * 75 * sqrt(2) + 150, -70, 70, solid, blue
hline: 70, 0, 3 * 75 * sqrt(2) + 150, solid, blue
hline: 0, 75 * sqrt(2), 75 * sqrt(2) + 150, solid, blue
hline: 0, 3 * 75 * sqrt(2), 3 * 75 * sqrt(2) + 150, solid, blue
hline: 35, 0, 3 * 75 * sqrt(2) + 150, dashed, gray
hline: 0, 0, 3 * 75 * sqrt(2) + 150, dashed, gray
bar: (0, 80), 150, horizontal
text: 75, 85, "150 cm", top-center
bar: (-12, 35), 35, vertical 
text: -12, 52.5, "35 cm", center-left
bar: (480, 0), 70, vertical
text: 480, 35, "70 cm", center-right
:::
```



---


:::{plot}
width: 70%
function: (x**2 - 1) * exp(-x), f
xmin: -6
xmax: 6
ymin: -6
ymax: 6
ticks: off
point: (2 + sqrt(3), f(2 + sqrt(3)))
point: (2 - sqrt(3), f(2 - sqrt(3)))
tangent: 2 + sqrt(3), f
nocache:
:::



---



:::{plot}
width: 70%
function: x**3 * exp(-x), [-1, 3], blue
function: -x**3 * exp(-x), (-1, 3], red
endpoint_markers: true
nocache:
:::


---

### Example 8: Line through two points (new syntax)

The `line` directive now supports a third syntax: passing through two points.
This example shows all three syntaxes working together:

```markdown
:::{plot}
line: 1, 0, solid, black
line: (0, -2), (4, 2), dashed, blue
line: -0.5, (2, 1), dotted, red
point: (0, -2)
point: (4, 2)
point: (2, 1)
xmin: -5
xmax: 5
ymin: -5
ymax: 5
grid: on
xlabel: $x$
ylabel: $y$
:::
```

:::{plot}
line: 1, 0, solid, black
line: (0, -2), (4, 2), dashed, blue
line: -0.5, (2, 1), dotted, red
point: (0, -2)
point: (4, 2)
point: (2, 1)
xmin: -5
xmax: 5
ymin: -5
ymax: 5
grid: on
xlabel: $x$
ylabel: $y$
:::

- **Black line**: `y = x` using slope-intercept form `line: 1, 0`
- **Blue line**: through points (0, -2) and (4, 2) using new two-point form `line: (0, -2), (4, 2)`
- **Red line**: slope -0.5 through point (2, 1) using point-slope form `line: -0.5, (2, 1)`
