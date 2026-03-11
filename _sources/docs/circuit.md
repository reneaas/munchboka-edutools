# `circuit`


:::{circuit}
width: 40%
fontsize: 18
flow: right
layout: loop
unit: 0.5
circuit: series(U, R1, parallel(R2, R3))
:::



:::{circuit}
width: 40%
fontsize: 18
flow: right
layout: loop
unit: 0.5
circuit: series(U, parallel(R1, R2), R3)
:::

:::{circuit}
width: 40%
fontsize: 18
flow: right
layout: loop
unit: 0.5
circuit: series(U, parallel(R1, R2, series(R3, R4)))
nocache:
:::
