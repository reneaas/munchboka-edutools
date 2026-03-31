# `circuit` directive

The `circuit` directive generates electric circuit diagrams as inline SVG from a simple topology description. You describe the circuit as nested `series(...)` / `parallel(...)` expressions, and the directive renders it using LaTeX `circuitikz`.

## Basic usage

A simple series circuit with a battery and two resistors:

````markdown
:::{circuit}
width: 40%
circuit: series(U, R1, R2)
:::
````

:::{circuit}
width: 40%
circuit: series(U, R1, R2)
:::

## Syntax overview

````markdown
:::{circuit}
component: V1, battery, 12 V
component: R1, resistor, 1 kΩ
component: L1, lamp

circuit: series(V1, R1, parallel(L1, R2))
width: 80%
layout: loop
:::
````

### Component declaration

Components are declared with repeated `component:` (or `comp:`) lines:

```
component: ID, type, value, label
```

- **ID** — a unique identifier (e.g. `R1`, `V1`, `L1`)
- **type** — component type (see table below)
- **value** — optional display value (e.g. `1 kΩ`, `12 V`)
- **label** — optional custom label (defaults to TeX-ified ID, e.g. `R1` → $R_1$)

If a component is referenced in `circuit:` but not explicitly declared, its type is inferred from the ID prefix.

### Component types

| Type keyword | Rendered as |
|---|---|
| `resistor`, `r`, `res` | Resistor |
| `var_resistor`, `pot`, `potmeter` | Variable resistor |
| `battery`, `source`, `dc`, `vsource` | Battery / voltage source |
| `lamp`, `bulb` | Lamp |
| `led` | LED |
| `diode` | Diode |
| `wire` | Plain wire (default) |

### ID prefix auto-detection

| Prefix | Inferred type |
|---|---|
| `R` | resistor |
| `RV` | var_resistor |
| `V`, `U` | battery |
| `L` | lamp |
| `D`, `LED` | led |

### Topology expression

The `circuit:` line uses nested function calls:

- `series(A, B, C)` — components in series
- `parallel(A, B, C)` — components in parallel
- Arguments can be component IDs or nested `series(...)`/`parallel(...)` groups

## Options

| Option | Meaning | Default |
|---|---|---|
| `width` | CSS width | — |
| `align` | `left`, `center`, or `right` | `center` |
| `layout` | `ladder` or `loop` | `ladder` |
| `flow` | Direction of current flow: `right`, `left`, `up`, `down` | `right` |
| `unit` | Scale factor (float) | `1.2` |
| `style` | `european` or `american` (circuitikz) | `european` |
| `backend` | `circuitikz` or `schemdraw` | `circuitikz` |
| `symbols` | `iec` or `ieee` (schemdraw only) | `iec` |
| `branch` | Parallel branch placement: `auto`, `up`, `down`, `both` | `auto` |
| `junctions` | Show junction dots: `true`/`false` | `true` |
| `fontsize` | Font size for labels | — |
| `class` | Extra CSS classes | — |
| `name` | Stable anchor / reference name | — |
| `alt` | Alt text for accessibility | — |
| `nocache` | Force regeneration | — |
| `debug` | Keep debug output | — |

## Examples

### Series with parallel branch

````markdown
:::{circuit}
width: 40%
fontsize: 18
flow: right
layout: loop
unit: 0.5
circuit: series(U, R1, parallel(R2, R3))
:::
````

:::{circuit}
width: 40%
fontsize: 18
flow: right
layout: loop
unit: 0.5
circuit: series(U, R1, parallel(R2, R3))
:::

### Parallel first, then series

````markdown
:::{circuit}
width: 40%
fontsize: 18
flow: right
layout: loop
unit: 0.5
circuit: series(U, parallel(R1, R2), R3)
:::
````

:::{circuit}
width: 40%
fontsize: 18
flow: right
layout: loop
unit: 0.5
circuit: series(U, parallel(R1, R2), R3)
:::

### Deeply nested parallel-series

````markdown
:::{circuit}
width: 40%
fontsize: 18
flow: right
layout: loop
unit: 0.5
circuit: series(U, parallel(R1, R2, series(R3, R4)))
nocache:
:::
````

:::{circuit}
width: 40%
fontsize: 18
flow: right
layout: loop
unit: 0.5
circuit: series(U, parallel(R1, R2, series(R3, R4)))
nocache:
:::

## Tips

- Components not declared with `component:` but referenced in `circuit:` are auto-detected from their ID prefix.
- Labels default to TeX formatting: `R1` → $R_1$, `RV12` → $RV_{12}$.
- The `circuitikz` backend requires a working LaTeX installation with the `circuitikz` package.
- Use `layout: loop` for perimeter-style layouts (current flows around a loop) and `layout: ladder` for ladder-style layouts.

## Source

[`src/munchboka_edutools/directives/circuit.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/circuit.py)
