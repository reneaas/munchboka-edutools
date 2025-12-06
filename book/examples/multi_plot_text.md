# multi-plot text examples

This document demonstrates the `text` keyword for the `multi-plot` directive.

## Example 1: Basic text annotation

```{multi-plot}
:functions: x**2, x**3
:fn_labels: f, g
:rows: 1
:cols: 2
:domains: (-2, 2), (-2, 2)
:xlims: (-2, 2), (-2, 2)
:ylims: (-1, 5), (-5, 5)

text: 1, 1, "Point A", 1
text: -1, 1, "Point B", 2
```

## Example 2: Text with placement

```{multi-plot}
:functions: sin(x), cos(x)
:fn_labels: f, g
:rows: 1
:cols: 2
:domains: (0, 6.28), (0, 6.28)
:xlims: (0, 6.28), (0, 6.28)
:ylims: (-1.5, 1.5), (-1.5, 1.5)

text: 1.57, 1, "Peak", top-center, 1
text: 0, 1, "Start", top-left, 2
```

## Example 3: Multiple text annotations on same axis

```{multi-plot}
:functions: x**2, 2*x
:fn_labels: f, g
:rows: 1
:cols: 2
:domains: (-3, 3), (-3, 3)
:xlims: (-3, 3), (-3, 3)
:ylims: (-1, 9), (-7, 7)

text: 0, 0, "Vertex", bottom-center, 1
text: -2, 4, "Left", top-right, 1
text: 2, 4, "Right", top-left, 1
```

## Example 4: Text on all axes

```{multi-plot}
:functions: x, x**2, x**3, x**4
:fn_labels: f, g, h, k
:rows: 2
:cols: 2
:domains: (-2, 2), (-2, 2), (-2, 2), (-2, 2)
:xlims: (-2, 2), (-2, 2), (-2, 2), (-2, 2)
:ylims: (-2, 2), (-1, 4), (-8, 8), (-1, 16)

text: 0, 0, "Origin"
```

## Example 5: Long placement variants

```{multi-plot}
:functions: exp(x), log(x)
:fn_labels: f, g
:rows: 1
:cols: 2
:domains: (-2, 2), (0.1, 5)
:xlims: (-2, 2), (0, 5)
:ylims: (0, 8), (-2, 2)

text: 0, 1, "e^0=1", longtop-left, 1
text: 1, 0, "ln(1)=0", longbottom-right, 2
```

## Example 6: Text with expressions

```{multi-plot}
:functions: sqrt(x), x**(1/3)
:fn_labels: f, g
:rows: 1
:cols: 2
:domains: (0, 9), (-8, 8)
:xlims: (0, 9), (-8, 8)
:ylims: (0, 3), (-2, 2)

text: 4, sqrt(4), "sqrt(4)=2", top-left, 1
text: 8, 2, "2^3=8", bottom-right, 2
```
