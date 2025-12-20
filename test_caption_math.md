# Test Caption Math Rendering

## Plot with Math in Caption

:::{plot}
width: 70%
function: x**2, f(x) = x^2
xmin: -3
xmax: 3
ymin: -1
ymax: 10

This plot shows the function $f(x) = x^2$ with a caption containing math: $\int_0^1 x^2 dx = \frac{1}{3}$.
:::

## Factor Tree with Math Caption

:::{factor-tree}
width: 50%
value: 72

The prime factorization is $72 = 2^3 \cdot 3^2$.
:::

## Sign Chart with Math Caption

:::{signchart}
width: 60%
points: -2, 1, 3
signs: -, +, -, +

Sign chart for $(x+2)(x-1)(x-3)$ showing intervals where $f(x) > 0$ and $f(x) < 0$.
:::
