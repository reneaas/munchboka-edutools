# Test Function Domain and Endpoint Support

## Test 1: Basic Domain with Closed Endpoints

```{plot}
:function-endpoints: true
:xmin: -5
:xmax: 5
:ymin: -5
:ymax: 5

function: x**2, [-2, 2], blue
```

## Test 2: Domain with Mixed Brackets

```{plot}
:function-endpoints: true
:xmin: -5
:xmax: 5
:ymin: -5
:ymax: 5

function: sin(x), [-pi, pi), red
function: cos(x), (-pi, pi], blue
```

## Test 3: Exclusions

Note: Exclusions use backslash-brace notation: `\{0}` excludes x=0.

```{plot}
:function-endpoints: true
:xmin: -5
:xmax: 5
:ymin: -5
:ymax: 5

function: 1/x, \\{0}, green
```

## Test 4: Interactive Graph with Domain

```{interactive-graph}
:function-endpoints: true
:xmin: -5
:xmax: 5
:ymin: -5
:ymax: 5

interactive-var: a, 0, 2, 20

function: -x**2 + a * x, (-3, a), blue
point: (a/2, -(a/2)**2 + a * (a/2))
```

## Test 5: Animate with Domain

```{animate}
:function-endpoints: true
:xmin: -5
:xmax: 5
:ymin: -5
:ymax: 5

animate-var: k, -2, 2, 30

function: x**2 + k, [-2, 2], blue
```

## Test 6: Function with Label and Domain

```{plot}
:function-endpoints: true
:xmin: -5
:xmax: 5
:ymin: -5
:ymax: 5

function: x**3, f, [-1, 1], red
point: (0.5, 0.5**3)
```
