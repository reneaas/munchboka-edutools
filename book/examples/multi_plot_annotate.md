# multi-plot annotate examples

This document demonstrates the `annotate` keyword for the `multi-plot` directive.

## Example 1: Basic arrow annotation

```{multi-plot}
:functions: x**2, x**3
:fn_labels: f, g
:rows: 1
:cols: 2
:domains: (-2, 2), (-2, 2)
:xlims: (-2, 2), (-2, 2)
:ylims: (-1, 5), (-5, 5)

annotate: (1, 2), (1, 1), "Minimum", 1
annotate: (-1, 2), (-1, 1), "Also here", 2
```

## Example 2: Arrow annotation with custom arc

```{multi-plot}
:functions: sin(x), cos(x)
:fn_labels: f, g
:rows: 1
:cols: 2
:domains: (0, 6.28), (0, 6.28)
:xlims: (0, 6.28), (0, 6.28)
:ylims: (-1.5, 1.5), (-1.5, 1.5)

annotate: (2, 1.3), (1.57, 1), "Peak", 0.5, 1
annotate: (5, -1.3), (4.71, -1), "Valley", 0.5, 2
```

## Example 3: Multiple annotations on same axis

```{multi-plot}
:functions: x**2, 2*x
:fn_labels: f, g
:rows: 1
:cols: 2
:domains: (-3, 3), (-3, 3)
:xlims: (-3, 3), (-3, 3)
:ylims: (-1, 9), (-7, 7)

annotate: (-1, 3), (0, 0), "Vertex", 0.3, 1
annotate: (1, 2.5), (-2, 4), "Left side", 0.2, 1
annotate: (-1, 2.5), (2, 4), "Right side", 0.2, 1
```

## Example 4: Annotations on all axes

```{multi-plot}
:functions: x, x**2, x**3, x**4
:fn_labels: f, g, h, k
:rows: 2
:cols: 2
:domains: (-2, 2), (-2, 2), (-2, 2), (-2, 2)
:xlims: (-2, 2), (-2, 2), (-2, 2), (-2, 2)
:ylims: (-2, 2), (-1, 4), (-8, 8), (-1, 16)

annotate: (-1.5, 1), (0, 0), "Origin"
```

## Example 5: Annotations with expressions

```{multi-plot}
:functions: sin(x), cos(x)
:fn_labels: f, g
:rows: 1
:cols: 2
:domains: (0, 2*pi), (0, 2*pi)
:xlims: (0, 6.5), (0, 6.5)
:ylims: (-1.5, 1.5), (-1.5, 1.5)

annotate: (pi/2 + 0.5, 1.2), (pi/2, sin(pi/2)), "Maximum", 0.3, 1
annotate: (pi + 0.5, 1.2), (pi, cos(pi)), "Minimum", 0.3, 2
```

## Example 6: Different arc curvatures

```{multi-plot}
:functions: exp(x), log(x)
:fn_labels: f, g
:rows: 1
:cols: 2
:domains: (-2, 2), (0.1, 5)
:xlims: (-2, 2), (0, 5)
:ylims: (0, 8), (-2, 2)

annotate: (-1, 5), (0, 1), "Point", 0.8, 1
annotate: (2, 1.5), (1, 0), "Origin", -0.5, 2
```
