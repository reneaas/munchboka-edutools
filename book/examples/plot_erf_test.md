# Test av erf-funksjonen

Denne siden tester at `erf(x)` fungerer i plot-direktivet.

:::{plot}
function: erf(x)
xmin: -3
xmax: 3
ymin: -1.5
ymax: 1.5
grid: true
xlabel: $x$
ylabel: $\text{erf}(x)$
:::

Error function er definert som:

$$
\text{erf}(x) = \frac{2}{\sqrt{\pi}} \int_0^x e^{-t^2} dt
$$
