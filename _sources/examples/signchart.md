# `signchart` directive

The `signchart` directive generates visual sign charts (fortegnsskjema in Norwegian) for polynomial functions. Sign charts show where a function is positive (+), negative (-), or zero (0).

## Basic Usage

### Quadratic Function

```{signchart}
---
function: x**2 - 4, f(x)
factors: true
width: 80%
---
Sign chart for f(x) = x² - 4
```

### Cubic Function

```{signchart}
---
function: x**3 - x, g(x)
factors: true
width: 80%
---
Sign chart for g(x) = x³ - x
```

## Without Factors

You can hide the factored form by setting `factors: false`:

```{signchart}
---
function: x**2 - 9
factors: false
width: 70%
---
Sign chart without factors shown
```

## Different Widths

### Full Width

```{signchart}
---
function: x**2 - 1, h(x)
width: 100%
---
Full width sign chart
```

### Fixed Width

```{signchart}
---
function: (x-1)*(x-2)*(x-3), p(x)
width: 600px
---
Fixed width sign chart (600px)
```

## Higher Degree Polynomials

### Quartic Function

```{signchart}
---
function: x**4 - 5*x**2 + 4, f(x)
factors: true
width: 85%
---
Sign chart for f(x) = x⁴ - 5x² + 4
```

### Quintic Function

```{signchart}
---
function: x**5 - 5*x**3 + 4*x, g(x)
factors: true
width: 90%
---
Sign chart for g(x) = x⁵ - 5x³ + 4x
```

## Custom Domain

You can restrict the sign chart to a specific interval using `xmin` and `xmax`:

```{signchart}
---
function: -3/2 * k**2 + 9/2, A'(k)
xmin: 0
xmax: 3
width: 100%
---
Sign chart for A'(k) restricted to domain [0, 3]
```

This is useful when:
- The function has a restricted domain in the problem context
- You only want to show behavior in a specific interval
- The function represents a real-world quantity with physical constraints

Another example with a rational function derivative:

```{signchart}
---
function: (-8 * r**2 + 160) / (r**2 + 20)**2, A'(r)
xmin: 0
xmax: 10
width: 100%
---
Sign chart for A'(r) on [0, 10]
```

## Features

### Automatic Factorization

The directive automatically factors the polynomial and shows:
- All zeros (roots) of the function
- The sign of the function in each interval
- The factored form (when `factors: true`)

### Caching

Sign charts are cached as SVG files to speed up rebuilds. To force regeneration:

```markdown
```{signchart}
---
function: x**2 - 4, f(x)
nocache: true
---
```
```

### Accessibility

- Alt text defaults to "Fortegnsskjema" (Sign chart)
- Can be customized with the `alt` option
- SVG includes `role="img"` and `aria-label` for screen readers

## Options Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `function` | string (required) | - | Polynomial expression and optional label |
| `factors` | boolean | `true` | Show factored form |
| `xmin` | number | auto | Minimum x-value for domain |
| `xmax` | number | auto | Maximum x-value for domain |
| `width` | string | auto | Width (e.g., "80%", "600px", "500") |
| `align` | string | `center` | Alignment: "left", "center", "right" |
| `alt` | string | "Fortegnsskjema" | Alt text for accessibility |
| `nocache` | flag | - | Force regeneration of chart |
| `class` | string | - | Additional CSS classes |
| `name` | string | - | Reference name for cross-referencing |

## Syntax

### YAML Front-matter Style

```markdown
```{signchart}
---
function: expression, label
factors: true
width: 80%
---
Caption text
```
```

### Simple Key-Value Style

```markdown
```{signchart}
function: expression, label
factors: true
width: 80%

Caption text
```
```

## Function Format

The `function` option accepts two formats:

1. **String with comma**: `"expression, label"`
   - Example: `"x**2 - 4, f(x)"`
   
2. **Tuple/list**: `("expression", "label")`
   - Example: `("x**2 - 4", "f(x)")`

The label is optional. If omitted, no function name is shown in the chart.

## Dependencies

This directive requires the `signchart` Python package to be installed:

```bash
pip install signchart
```

The package uses SymPy for symbolic mathematics and Matplotlib for rendering.





:::{signchart}
width: 100%
function: (x**2 - 1) / (exp(x) - 1), f(x)
nocache:
:::
