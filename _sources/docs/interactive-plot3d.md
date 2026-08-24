# `interactive-plot3d` directive

The `interactive-plot3d` directive creates an interactive 3D figure with one or more sliders. It uses the slider syntax from `interactive-graph` and the drawing syntax from `plot3d-2`.

Frames are pre-rendered during the Sphinx/Jupyter Book build. The browser then swaps SVG deltas as the slider moves, so the final page does not need Python or Matplotlib at runtime.

## Basic usage

````markdown
:::{interactive-plot3d}
width: 70%
interactive-var: a, 0, 2, 5
interactive-var: rot, -90, 90, 10
interactive-var: elev, -90, 90, 10 
interactive-var-start: a=1, rot=-60, elev=20
xrange: (-1, 3)
yrange: (-1, 2)
zrange: (-1, 2)
axis: on
grid: true
vector: (0, 0, 0), (a, 1, 1), blue
point: (a, 1, 1), red
text: at=(a, 1, 1), value="$P$", offset=(0.1, 0.1, 0.1)

Et punkt og en vektor som styres av skyveknappen.
:::
````

:::{interactive-plot3d}
nocache:
width: 70%
interactive-var: a, 0, 2, 5
interactive-var: elev, -90, 90, 10
interactive-var: azim, -90, 90, 10 
interactive-var-start: a=1, elev=-60, azim=20
xrange: (-1, 3)
yrange: (-1, 2)
zrange: (-1, 2)
axis: on
grid: true
vector: (0, 0, 0), (a, 1, 1), blue
point: (a, 1, 1), red
text: at=(a, 1, 1), value="$P$", offset=(0.1, 0.1, 0.1)
elev: elev
azim: azim

Et punkt og en vektor som styres av skyveknappen.
:::

## Syntax overview

Use the same key-value block format as `plot3d-2`:

````markdown
:::{interactive-plot3d}
interactive-var: name, min, max, frames
interactive-var-start: value

plot3d-2-key: value
plot3d-2-key: value

Optional caption text.
:::
````

### Interactive variable

The `interactive-var` key defines a slider:

```text
interactive-var: name, min, max, frames
```

| Part | Meaning |
|---|---|
| `name` | Variable name used in expressions, for example `a`, `t`, `theta`, or `N` |
| `min` | Minimum slider value |
| `max` | Maximum slider value |
| `frames` | Number of pre-rendered frames; must be at least `2` |

By default, the initial value is the middle frame. Use `interactive-var-start` to choose the initial slider position:

```text
interactive-var-start: 1.5
```

For multiple variables, repeat `interactive-var`:

````markdown
:::{interactive-plot3d}
interactive-var: a, 0, 2, 5
interactive-var: b, -1, 1, 5
interactive-var-start: a=1, b=0
point: (a, b, a*b), red
:::
````

The total number of generated frames is the product of all slider frame counts.

## Supported drawing keys

`interactive-plot3d` supports the same drawing and macro keys as `plot3d-2`:

- `angle`
- `curve`
- `line`
- `line-segment`
- `ngon`
- `normal-segment`
- `point`
- `plane`
- `prism`
- `pyramid`
- `right-angle`
- `sphere`
- `solid-of-revolution`
- `text`
- `vector`
- `let`
- `def`
- `repeat`
- `macro`
- `use`
- `endmacro`

Most numeric fields can use the interactive variable directly:

````markdown
:::{interactive-plot3d}
interactive-var: r, 0.5, 2, 7
xrange: (-3, 3)
yrange: (-3, 3)
zrange: (-1, 3)
sphere: center=(0, 0, 1), radius=r, color=skyblue, alpha=0.45
text: at=(0, 0, 1 + r), value="$r = {r:.1f}$"
:::
````

Camera options can also be interactive. This is the standard way to make a rotatable pre-rendered 3D figure:

````markdown
:::{interactive-plot3d}
interactive-var: azim, -80, 40, 25
interactive-var-start: -40
elev: 25
azim: azim
xrange: (-2, 2)
yrange: (-2, 2)
zrange: (-1, 3)
vector: (0, 0, 0), (1, 1, 2), blue
point: (1, 1, 2), red
:::
````

## Options

The directive accepts the global `plot3d-2` options plus these interactive options:

| Option | Meaning | Default |
|---|---|---|
| `interactive-var` | Slider variable: `name, min, max, frames` | required |
| `interactive-var-start` | Initial slider value, or `a=..., b=...` for multiple variables | middle frame |
| `interactive-max-frames` | Safety limit for multi-variable frame generation | `10000` |
| `interactive-workers` | Number of worker processes, `0`, or `auto` | auto |
| `parallel` | Enable parallel rendering for single-variable figures | `false` |
| `height` | CSS height for the rendered SVG | `auto` |
| `nocache` | Force regeneration of frame assets | off |

Common `plot3d-2` options include `width`, `align`, `alt`, `figsize`, `xrange`, `yrange`, `zrange`, `elev`, `azim`, `zoom`, `axis`, `grid`, `ticks`, `fontsize`, `lw`, and `usetex`.

## Examples

### Moving point on a helix

````markdown
:::{interactive-plot3d}
width: 65%
interactive-var: t0, 0, 2*pi, 25
xrange: (-1.5, 1.5)
yrange: (-1.5, 1.5)
zrange: (0, 7)
axis: on
curve: x=cos(t), y=sin(t), z=t, trange=(0, 2*pi), color=#2468ac, samples=96
point: (cos(t0), sin(t0), t0), red
vector: (0, 0, 0), (cos(t0), sin(t0), t0), blue
text: at=(cos(t0), sin(t0), t0), value="$t = {t0:.2f}$", offset=(0.1, 0.1, 0.1)
:::
````

### Plane with changing height

````markdown
:::{interactive-plot3d}
interactive-var: h, -1, 2, 7
xrange: (-2, 2)
yrange: (-2, 2)
zrange: (-2, 3)
axis: on
plane: equation=z = h, color=orange, alpha=0.35
point: (0, 0, h), red
text: at=(0, 0, h), value="$z = {h:.1f}$", offset=(0.15, 0.15, 0.15)
:::
````

### Rotate around the vertical axis

````markdown
:::{interactive-plot3d}
interactive-var: azim, -80, 40, 25
interactive-var-start: -40
width: 65%
elev: 25
azim: azim
xrange: (-2, 2)
yrange: (-2, 2)
zrange: (-1, 3)
axis: on
plane: equation=z = x + y, color=orange, alpha=0.3
vector: (0, 0, 0), (1, 1, 2), blue
point: (1, 1, 2), red
:::
````

## Build-time notes

- Every frame is rendered at build time, so large frame counts can slow down builds.
- Camera-driven sliders that affect `azim`, `elev`, or `zoom` store full SVG frames instead of compact structural deltas. This is larger, but it avoids brittle diffs when the entire 3D projection changes.
- Use `interactive-max-frames` as a guard for multi-variable examples.
- Add `nocache` while developing if you need to force frame regeneration.
- Set `usetex: false` in examples that should build without a local LaTeX installation.

The implementation lives in [src/munchboka_edutools/directives/interactive_plot3d.py](/Users/reneaas/codes/vgs_books/munchboka-edutools/src/munchboka_edutools/directives/interactive_plot3d.py).
