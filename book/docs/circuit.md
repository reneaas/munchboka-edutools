# `circuit`


:::{circuit}
width: 70%
fontsize: 30
flow: right          # right|left|up|down
layout: loop       # ladder|loop
unit: 1.1
circuit: series(V1, R1, parallel(L1, series(D1, R2)), RV1)
nocache:
:::



:::{circuit}
width: 70%
fontsize: 26
flow: right
layout: loop
unit: 1
circuit: series(V, R1, R2, R3, R4, R5, R6, L1)
nocache:
:::


:::{circuit}
width: 70%
fontsize: 26
flow: right
layout: loop
unit: 1
circuit: series(V, R1, parallel(R2, R3), R4, R5, L1)
nocache:
:::