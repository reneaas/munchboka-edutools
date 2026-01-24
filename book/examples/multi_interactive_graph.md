# Multi Interactive Graph

The `multi-interactive-graph` directive creates multiple synchronized interactive graphs that share a single slider control. This is useful for comparing how different functions respond to the same parameter changes.

## Basic Syntax

````markdown
::::{multi-interactive-graph}
---
rows: 1
cols: 2
interactive-var: a, -5, 5, 50
---

:::{interactive-graph}
function: x**2 + a*x
xmin: -10
xmax: 10
:::

:::{interactive-graph}
function: sin(a*x)
xmin: -10
xmax: 10
:::
::::
````

## Features

- **Synchronized slider**: All graphs update simultaneously
- **Grid layout**: Organize graphs in rows and columns
- **Shared variable**: All graphs use the same interactive variable
- **Reuses features**: Each graph supports all features from `interactive-graph` (functions, points, tangents, text)

## Options

### Container Options (in frontmatter)

- `interactive-var`: **(required)** Format: `name, min, max, frames`
  - Example: `a, -5, 5, 50` creates 50 frames from a=-5 to a=5
- `rows`: Number of rows in the grid (default: 1)
- `cols`: Number of columns in the grid (default: number of graphs)
- `width`: Width of the entire container (default: "100%")
- `height`: Height of individual graphs (default: "auto")
- `align`: Alignment of the container (default: "center")

### Individual Graph Options

Each nested `interactive-graph` supports all options from the standard directive:
- `function`: Plot functions
- `point`: Add points
- `tangent`: Draw tangent lines
- `text`: Add text annotations with f-string formatting
- `xmin`, `xmax`, `ymin`, `ymax`: Set axis ranges
- `grid`: Enable/disable grid

## Examples

### Example 1: Side-by-Side Comparison

Compare a polynomial and a trigonometric function:

::::{multi-interactive-graph}
---
rows: 1
cols: 2
interactive-var: a, -4, 4, 50
---

:::{interactive-graph}
function: x**3 - 3*x + 2, f
ymin: -10
ymax: 10
xmin: -5
xmax: 5
point: (a, f(a))
tangent: a, f, solid, red
text: 2, -6, "a = {a:.2f}", center-center
grid: true
:::

:::{interactive-graph}
function: sin(a*x)
xmin: -10
xmax: 10
ymin: -2
ymax: 2
point: (a, sin(a*a))
text: 2, 1.5, "a = {a:.2f}", center-center
grid: true
:::
::::

### Example 2: 2×2 Grid of Functions

Explore four different function families:

::::{multi-interactive-graph}
---
rows: 2
cols: 2
interactive-var: a, -3, 3, 40
---

:::{interactive-graph}
function: x**2 + a*x
xmin: -5
xmax: 5
ymin: -10
ymax: 10
grid: true
:::

:::{interactive-graph}
function: a*x**3
xmin: -3
xmax: 3
ymin: -10
ymax: 10
grid: true
:::

:::{interactive-graph}
function: sin(a*x)
xmin: -6.28
xmax: 6.28
ymin: -2
ymax: 2
grid: true
:::

:::{interactive-graph}
function: exp(a*x/5)
xmin: -5
xmax: 5
ymin: 0
ymax: 5
grid: true
:::
::::

### Example 3: With Text Annotations

All graphs can use text with f-string formatting:

::::{multi-interactive-graph}
---
rows: 1
cols: 3
interactive-var: k, 0, 2, 30
---

:::{interactive-graph}
function: k*x
xmin: -5
xmax: 5
ymin: -10
ymax: 10
text: 2, 8, "y = {k:.2f}x", center-center
grid: true
:::

:::{interactive-graph}
function: x**2 + k
xmin: -5
xmax: 5
ymin: -5
ymax: 15
text: 2, 12, "y = x² + {k:.2f}", center-center
grid: true
:::

:::{interactive-graph}
function: k*x**2
xmin: -5
xmax: 5
ymin: -5
ymax: 15
text: 2, 12, "y = {k:.2f}x²", center-center
grid: true
:::
::::

## Technical Details

### Frame Generation

- Graphs are pre-rendered as SVG frames and stored in a delta-compressed format
- Storage (per tile): `_static/multi_interactive/<hash>/graph_<n>/base.svg` + `deltas.json`
- Multi-variable graphs also include: `meta.json`
- Caching: Assets are reused unless content changes or `nocache` is specified

### Performance

For `n` graphs with `f` frames each:
- Total frames: `n × f` (generated at build time)
- Runtime payload: `n` base SVGs + `n` delta JSON files (typically much smaller than full-frame assets)

Example: 4 graphs × 50 frames = 200 frames (but shipped as deltas)

### Browser Compatibility

- Tested on: Chrome, Firefox, Safari, Edge
- Requires: JavaScript enabled
- Mobile: Touch-friendly slider with responsive layout

## Tips

1. **Frame count**: Use 30-50 frames for smooth interaction without excessive file size
2. **Grid layout**: For 2 graphs, use `cols: 2`; for 4 graphs, use `rows: 2, cols: 2`
3. **Text positioning**: Use text annotations to label each graph's function
4. **Axis ranges**: Set consistent ranges for easier comparison, or different ranges to focus on specific features
5. **Variable naming**: Use short, meaningful variable names (a, k, n, t)

## Comparison with animate

| Feature | multi-interactive-graph | animate in multi-plot2 |
|---------|------------------------|------------------------|
| Control | Single shared slider | Automatic playback |
| Interaction | User-controlled exploration | Watch animation loop |
| Frame access | Any frame instantly | Sequential playback |
| Best for | Comparing functions | Showing time evolution |
| File format | SVG + delta JSON | WebP/GIF animation |

## See Also

- [Interactive Graph](interactive_graph.md) - Single interactive graph with slider
- [Animate](animate.md) - Animated plots with automatic playback
- [Multi Plot](multi_plot.md) - Static multi-panel plots
