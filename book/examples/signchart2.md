# Sign Chart 2 Examples

This page demonstrates the new `signchart-2` directive with enhanced features for polynomials, rational functions, and transcendental functions.

## Basic Polynomial Example

Simple quadratic function:

```{signchart-2}
---
function: x**2 - 4, f(x)
factors: true
width: 100%
---
Sign chart for $f(x) = x^2 - 4$
```

## Polynomial with Custom Label

Higher degree polynomial with a custom function name:

```{signchart-2}
---
function: x**3 - 3*x**2 - x + 3, g(x)
factors: true
width: 100%
---
Sign chart for $g(x) = x^3 - 3x^2 - x + 3$
```

## Rational Function

Sign chart for a rational function showing singularities:

```{signchart-2}
---
function: (x**2 - 1)/(x**2 - 4), h(x)
factors: true
width: 100%
---
Sign chart for $h(x) = \frac{x^2 - 1}{x^2 - 4}$ showing zeros and poles
```

## Transcendental Function with Domain

Sign chart for trigonometric function with specified domain:

```{signchart-2}
---
function: sin(x)*cos(x), f(x)
domain: (-3.5, 3.5)
factors: true
width: 100%
---
Sign chart for $f(x) = \sin(x) \cdot \cos(x)$ over domain $[-3.5, 3.5]$
```

## Exponential and Logarithm

Combining exponential and polynomial:

```{signchart-2}
---
function: (x - 1)*exp(-x), p(x)
domain: (-2, 5)
factors: true
width: 100%
---
Sign chart for $p(x) = (x-1)e^{-x}$
```

## Compact Format

Using `small_figsize` for a more compact chart without factors:

```{signchart-2}
---
function: x**2 - 9, f(x)
factors: false
small_figsize: true
width: 80%
---
Compact sign chart without factors
```

## Generic Labels

Using generic labels ($x_1, x_2, \ldots$) instead of exact root values:

```{signchart-2}
---
function: x**3 - 2*x, f(x)
generic_labels: true
factors: true
width: 100%
---
Sign chart with generic labels for roots
```

## Black and White Chart

Monochrome sign chart (useful for printing):

```{signchart-2}
---
function: x**4 - 5*x**2 + 4, f(x)
color: false
factors: true
width: 100%
---
Black and white sign chart
```

## Complex Rational Function

Multiple zeros and poles:

```{signchart-2}
---
function: (x**2 - 1)*(x - 3)/((x + 2)*(x - 2)), r(x)
factors: true
width: 100%
---
Sign chart for $r(x) = \frac{(x^2-1)(x-3)}{(x+2)(x-2)}$
```

## Sine Function

Pure trigonometric function over multiple periods:

```{signchart-2}
---
function: sin(x), f(x)
domain: (-7, 7)
factors: false
width: 100%
---
Sign chart for $f(x) = \sin(x)$ over $[-7, 7]$
```

## Custom Figure Size

Explicitly setting figure dimensions:

```{signchart-2}
---
function: x**3 - x, f(x)
factors: true
figsize: (10, 4)
width: 100%
---
Sign chart with custom figure size $(10, 4)$ inches
```

## Comparison: Original vs Signchart-2

### Using original signchart directive

```{signchart}
---
function: x**2 - 4, f(x)
factors: true
width: 100%
---
Original signchart directive (requires external package)
```

### Using new signchart-2 directive

```{signchart-2}
---
function: x**2 - 4, f(x)
factors: true
width: 100%
---
New signchart-2 directive (embedded plotting logic)
```

## Advanced Examples

### Product of Linear and Transcendental

```{signchart-2}
---
function: x*sin(x), f(x)
domain: (-10, 10)
factors: true
width: 100%
---
Sign chart for $f(x) = x \sin(x)$
```

### Rational with Transcendental

```{signchart-2}
---
function: cos(x)/(x**2 - 1), g(x)
domain: (-3, 3)
factors: true
width: 100%
---
Sign chart for $g(x) = \frac{\cos(x)}{x^2 - 1}$
```

### High Degree Polynomial

```{signchart-2}
---
function: (x - 1)*(x + 1)*(x - 2)*(x + 2)*(x - 3), p(x)
factors: true
width: 100%
---
Sign chart for fifth-degree polynomial
```

## Features Comparison Table

| Feature | signchart | signchart-2 |
|---------|-----------|-------------|
| Polynomial support | ✓ | ✓ |
| Rational functions | Limited | ✓ |
| Transcendental functions | ✗ | ✓ |
| Custom domain | Limited | ✓ |
| Generic labels | ✗ | ✓ |
| Color control | ✗ | ✓ |
| Custom figsize | ✗ | ✓ |
| External dependency | Required | None |
| Factor display | ✓ | ✓ |

## Notes

- The `domain` parameter is particularly useful for transcendental functions where numerical methods are needed to find zeros
- Generic labels are helpful when exact root values are complex or when you want a cleaner presentation
- The directive automatically handles singularities (poles) in rational functions
- Factor display works for all function types, not just polynomials
