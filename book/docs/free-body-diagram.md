# `free-body-diagram` directive

:::{free-body-diagram}
object: ball, size=1.6, position=(0, 0), color=teal
velocity: angle=30
force: gravity, length=0.5, name="$\vec G$"
force: normal, length=0.4, name="$\vec N$"
force: friction, length=0.25, name="$\vec R$"
force: air-resistance, length=0.3, name="$\vec L$"
width: 60%
:::

The `free-body-diagram` directive composes a physics free-body diagram —
an object outline, force vectors with correct points of attack, and a small
corner axis indicator — from a compact key-value syntax. It does not draw
anything itself: it generates ordinary [`plot`](plot.md) primitives
(`polygon`, `circle`, `vector`, `text`) and delegates all rendering, caching,
and figure options (`width`, `align`, `name`, captions, ...) to the `plot`
directive, so anything `plot` supports for those is available here too.

## Basic usage

```markdown
:::{free-body-diagram}
object: ball, size=1.6, position=(0, 0), color=teal
velocity: angle=30
force: gravity, length=0.5, name="$\vec G$"
force: normal, length=0.4, name="$\vec N$"
force: friction, length=0.25, name="$\vec R$"
force: air-resistance, length=0.3, name="$\vec L$"
width: 60%
:::
```

- `object:` is required, exactly once — the thing the diagram is drawn around.
- `force:` is required, at least once — one line per force vector.
- `velocity:` is optional — it only matters for forces whose direction depends
  on the direction of motion (`friction`, `air-resistance`).

## Syntax overview

```text
object: ball|square|toy-car, size=1, position=(0, 0), color=.., alpha=..
velocity: angle=<degrees>          # or: velocity: (dx, dy)
force: <kind>, length=.., name="$..$", color=.., point=(x, y), direction=..
axis-indicator: true|false         # default true
```

Every other `key: value` line (`width`, `align`, `name`, `fontsize`, `lw`,
`class`, `nocache`, `usetex`, `handdrawn`, `xstep`, `ystep`, `ticks`, `grid`, ...)
is forwarded straight to the delegated `plot` directive — see
[the `plot` directive's global options](plot.md#global-options) for the full
list. `xmin`/`xmax`/`ymin`/`ymax` are computed automatically from the object
and force geometry (with padding), but an explicit value here overrides that.
Lines after the first blank line become the figure caption, exactly like in
`plot`.

## Objects

| `object:` kind | `size` means | `position` is |
| --- | --- | --- |
| `ball` | diameter | the center of the ball (and its center of mass) |
| `square` | side length | the center of the square |
| `toy-car` | overall body length | the car's center of mass (a simple schematic: one body rectangle plus two wheels — nothing more detailed is drawn) |

`position` defaults to `(0, 0)`; `color` defaults to `black`; `alpha` (fill
opacity) is optional and uses `plot`'s own `polygon`/`circle` default when
omitted.

```markdown
:::{free-body-diagram}
object: toy-car, size=2, color=orange
velocity: (1, 0)
force: gravity, length=0.7, name="$\vec G$"
force: normal, length=0.5, name="$\vec N$"
force: friction, length=0.4, name="$\vec R$"
force: air-resistance, length=0.5, name="$\vec L$"
width: 60%
:::
```

which yields:

:::{free-body-diagram}
object: toy-car, size=2, color=orange
velocity: (1, 0)
force: gravity, length=0.7, name="$\vec G$"
force: normal, length=0.5, name="$\vec N$"
force: friction, length=0.4, name="$\vec R$"
force: air-resistance, length=0.5, name="$\vec L$"
width: 60%
:::

## Forces

Every `force:` line needs a `length=` and picks one of five kinds. Four of
them have a standard default point of attack and direction, derived from the
object's geometry and, where relevant, the `velocity:` line:

| `force:` kind | Default point | Default direction | Default `name=` | Default `color=` |
| --- | --- | --- | --- | --- |
| `gravity` | the object's center of mass | straight down | `$\vec G$` | `black` |
| `normal` | the contact point with the ground | straight up | `$\vec N$` | `blue` |
| `friction` | the contact point with the ground | opposes the horizontal component of `velocity:` | `$\vec R$` | `orange` |
| `air-resistance` | the point of the object facing the direction of motion | opposite `velocity:` | `$\vec L$` | `teal` |
| `custom` | none — `point=` is required | none — `direction=` is required | none | `purple` |

`friction` and `air-resistance` need a `velocity:` line to compute their
default point/direction; without one, give them an explicit `point=` and/or
`direction=` instead (kinetic friction's direction in particular is genuinely
case-dependent, so it is never guessed silently).

Any force — standard or `custom` — accepts these overrides:

- `point=(x, y)` — replace the computed attachment point.
- `direction=<degrees>` or `direction=(dx, dy)` — replace the computed direction
  (degrees are measured counter-clockwise from the positive x-axis).
- `color=` — any color `plot` understands.
- `name=` — the label text (plain text or `$math$`); omit it for no label.

```{tip}
Pick `length=` noticeably smaller than the object's own `size=` (roughly
0.2–0.5×) for the cleanest-looking arrows — a force vector longer than the
object it acts on will visually cross through the object's own outline.
```

## Velocity and automatic directions

`velocity:` sets the direction of motion used by `friction` and
`air-resistance`'s defaults:

```text
velocity: angle=20      # degrees, counter-clockwise from +x
velocity: (1, 0.3)      # an explicit (dx, dy) direction
```

Only its *direction* matters (it is normalized internally), so `(2, 0)` and
`(1, 0)` are equivalent.

## Custom forces

Use `force: custom` for anything outside the standard four — tension, an
applied push or pull, a spring force, and so on. Both `point=` and
`direction=` are required since there is no sensible default:

```markdown
:::{free-body-diagram}
object: square, size=1.4, color=purple, alpha=0.15
force: gravity, length=0.6, name="$\vec G$"
force: custom, length=0.5, name="$\vec T$", point=(0, 0.7), direction=90, color=green
:::
```

which yields:

:::{free-body-diagram}
object: square, size=1.4, color=purple, alpha=0.15
force: gravity, length=0.6, name="$\vec G$"
force: custom, length=0.5, name="$\vec T$", point=(0, 0.7), direction=90, color=green
:::

## Axis indicator

By default, a small pair of labeled arrows ("$x$"/"$y$") is drawn in the
bottom-left corner of the figure to indicate the positive axis directions —
the main plot's own axes are hidden (`axis: off`) so they don't clutter the
diagram, and `axis: equal` keeps the object's real proportions (a `ball`
actually looks circular). Disable it with:

```text
axis-indicator: false
```

## Limits

- Only a horizontal ground is supported (no incline/`surface-angle` option
  yet) — `normal` always points straight up and `friction` always acts along
  the x-axis.
- `size=`, `position=`, `length=`, `point=`, and `direction=` take plain
  numbers, not full SymPy expressions (unlike the underlying `plot`
  primitives this directive generates).
