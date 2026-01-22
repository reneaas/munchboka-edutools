# Angle Arc Test

Testing the new angle-arc and line-segment features in interactive-graph.

## Simple Quarter Circle

```{interactive-graph}
:xmin: -1
:xmax: 3
:ymin: -1
:ymax: 3
:var: a
:var-range: [0, 2, 0.1]
:initial-value: 1
:xlabel: x
:ylabel: y
:aspect-equal: true

angle-arc: (a, a), 1, 0, 90, solid, blue
point: a, a, open, black
```

## Full Circle with Animation

```{interactive-graph}
:xmin: -3
:xmax: 3
:ymin: -3
:ymax: 3
:var: t
:var-range: [0, 360, 10]
:initial-value: 90
:xlabel: x
:ylabel: y
:aspect-equal: true

angle-arc: (0, 0), 2, 0, t, solid, red
point: 2*cos(t*pi/180), 2*sin(t*pi/180), filled, red
```

## Multiple Arcs with Different Styles

```{interactive-graph}
:xmin: -3
:xmax: 3
:ymin: -3
:ymax: 3
:var: scale
:var-range: [0.5, 2, 0.1]
:initial-value: 1
:xlabel: x
:ylabel: y
:aspect-equal: true

angle-arc: (0, 0), scale, 0, 90, solid, blue
angle-arc: (0, 0), scale, 90, 180, dashed, green
angle-arc: (0, 0), scale, 180, 270, dotted, red
angle-arc: (0, 0), scale, 270, 360, dashdot, purple
```

## Line Segments

```{interactive-graph}
:xmin: -1
:xmax: 3
:ymin: -1
:ymax: 3
:var: t
:var-range: [0, 2, 0.1]
:initial-value: 1
:xlabel: x
:ylabel: y
:aspect-equal: true

line-segment: (0, 0), (t, t), solid, blue
line-segment: (0, t), (t, 0), dashed, red
point: t, t, filled, blue
point: t, 0, filled, red
point: 0, t, filled, green
```

## Combined: Arc with Radii

```{interactive-graph}
:xmin: -3
:xmax: 3
:ymin: -3
:ymax: 3
:var: angle
:var-range: [0, 360, 5]
:initial-value: 45
:xlabel: x
:ylabel: y
:aspect-equal: true

angle-arc: (0, 0), 2, 0, angle, solid, purple
line-segment: (0, 0), (2*cos(angle*pi/180), 2*sin(angle*pi/180)), solid, blue
line-segment: (0, 0), (2, 0), dashed, gray
point: 0, 0, filled, black
point: 2*cos(angle*pi/180), 2*sin(angle*pi/180), filled, purple
point: 2, 0, filled, gray
```

## Vectors - Legacy Format

```{interactive-graph}
:xmin: -1
:xmax: 4
:ymin: -1
:ymax: 4
:var: t
:var-range: [0, 3, 0.1]
:initial-value: 1
:xlabel: x
:ylabel: y
:aspect-equal: true

vector: 0, 0, t, t, red
vector: 1, 0, t, 0.5*t, blue
vector: 0, 1, 0.5*t, t, green
```

## Vectors - Point Format

```{interactive-graph}
:xmin: -1
:xmax: 3
:ymin: -1
:ymax: 3
:var: theta
:var-range: [0, 360, 10]
:initial-value: 45
:xlabel: x
:ylabel: y
:aspect-equal: true

vector: (0, 0), cos(theta*pi/180), sin(theta*pi/180), red
vector: (1, 1), cos(theta*pi/180), sin(theta*pi/180), blue
```

## Vectors - Two Points Format

```{interactive-graph}
:xmin: -1
:xmax: 3
:ymin: -1
:ymax: 3
:var: s
:var-range: [0, 2, 0.1]
:initial-value: 1
:xlabel: x
:ylabel: y
:aspect-equal: true

vector: (0, 0), (s, s), purple
vector: (0.5, 0), (0.5+s, s/2), teal
point: s, s, filled, purple
point: 0.5+s, s/2, filled, teal
```


