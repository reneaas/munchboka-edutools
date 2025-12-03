# Test av line-directive med uttrykk

Test at `line`-direktivet kan evaluere matematiske uttrykk.

:::{plot}
function: (x - 1)**2 + 2, f
line: (f(4) - f(1)) / 3, (1, f(1))
line: sqrt(2), 2 - sqrt(2)
xmin: -1
xmax: 5
ymin: -1
ymax: 12
grid: true
xlabel: $x$
ylabel: $y$
:::

Linjene skal være:
- Linje 1: stigningstall $(f(4) - f(1))/3 = (11 - 2)/3 = 3$ gjennom punktet $(1, f(1)) = (1, 2)$
- Linje 2: stigningstall $\sqrt{2} \approx 1.414$ og konstantledd $2 - \sqrt{2} \approx 0.586$
