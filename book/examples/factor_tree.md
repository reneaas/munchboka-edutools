# Factor Tree Examples

This page demonstrates the `factor-tree` directive, which creates visual representations of prime factorization using tree diagrams.

## Basic Usage

Default factor tree for 68:

```{factor-tree}
:n: 68
```

## Different Numbers

Factor tree for 24:

```{factor-tree}
:n: 24
```

Factor tree for 120:

```{factor-tree}
:n: 120
```

Factor tree for 84:

```{factor-tree}
:n: 84
```

## Custom Styling

Wider angle (40 degrees) and longer branches:

```{factor-tree}
:n: 96
:angle: 40
:branch_length: 2.2
```

Larger font size:

```{factor-tree}
:n: 72
:fontsize: 24
```

## Custom Sizing

Custom figure size (4x4 inches):

```{factor-tree}
:n: 108
:figsize: 4,4
```

Custom display width:

```{factor-tree}
:n: 60
:width: 500px
```

Percentage width:

```{factor-tree}
:n: 48
:width: 60%
:align: center
```

## Alignment

Left-aligned:

```{factor-tree}
:n: 36
:width: 300px
:align: left
```

Right-aligned:

```{factor-tree}
:n: 56
:width: 300px
:align: right
```

## With Captions

```{factor-tree}
:n: 144
:width: 80%

Prime factorization of 144 showing the factor tree breakdown.
```

## YAML-Style Configuration

```{factor-tree}
---
n: 180
angle: 35
fontsize: 20
figsize: 4.5,4.5
width: 70%
---

Factor tree for 180 using YAML-style configuration.
```

## Large Numbers

Factor tree for 360:

```{factor-tree}
:n: 360
:figsize: 5,5
:width: 80%
```

## Prime Numbers

When the number is prime, it shows just a single node:

```{factor-tree}
:n: 17
```

## Features

The factor tree directive:
- Automatically calculates prime factorization
- Creates visually appealing tree diagrams
- Supports customizable angles, branch lengths, and font sizes
- Generates responsive SVG graphics
- Includes accessibility features (ARIA labels)
- Uses content-based caching to avoid regeneration
- Supports captions and cross-references
