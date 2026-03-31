# `table` directive

The `table` directive creates simple data tables from comma-separated content. It supports transposition, per-column placement, inline math, and ellipsis expansion — making it ideal for textbook-style value tables.

## Basic usage

A table with labelled columns and rows of values:

````markdown
:::{table}
labels: $x$, $f(x)$, $g(x)$
1, 2, 3
4, 5, 6
7, 8, 9
:::
````

:::{table}
labels: $x$, $f(x)$, $g(x)$
1, 2, 3
4, 5, 6
7, 8, 9
:::

## Syntax overview

````markdown
:::{table}
---
transpose:
width: 80%
align: center
---
labels: x, y, z
placement: center, right, left
1, 2, 3
4, 5, 6
:::
````

### Content format

- The first `labels:` line defines the column (or row) headers.
- Each subsequent non-empty line is a comma-separated data row.
- `placement:` sets per-column text alignment (`left`, `center`, `right`).
- `width:` and `align:` can appear in either front-matter options or the content body.

## Options

| Option | Meaning |
|---|---|
| `transpose` | Swap rows and columns so labels become row headers |
| `width` | CSS width of the table frame (e.g. `80%`, `400px`) |
| `align` | Horizontal placement of the table: `left`, `center`, or `right` |
| `class` | Extra CSS classes |
| `name` | Stable anchor / reference name |

## Examples

### Transposed table

When `:transpose:` is set, labels become row headers instead of column headers:

````markdown
:::{table}
---
transpose:
---
labels: $x$, $f(x)$
-2, 4
-1, 1
0, 0
1, 1
2, 4
:::
````

:::{table}
---
transpose:
---
labels: $x$, $f(x)$
-2, 4
-1, 1
0, 0
1, 1
2, 4
:::


### Column alignment

Use `placement:` to control how each column is aligned. The ellipsis `...` repeats the preceding value for all remaining columns:

````markdown
:::{table}
labels: Term, Formula, Value
placement: left, center, ...
$a_1$, $2 \cdot 1$, 2
$a_2$, $2 \cdot 2$, 4
$a_3$, $2 \cdot 3$, 6
:::
````

:::{table}
labels: Term, Formula, Value
placement: left, center, ...
$a_1$, $2 \cdot 1$, 2
$a_2$, $2 \cdot 2$, 4
$a_3$, $2 \cdot 3$, 6
:::

### Ellipsis rows and cells

Use `...` as a full row to insert a vertical ellipsis, or inside a cell for horizontal ellipsis:

````markdown
:::{table}
labels: $n$, $a_n$
1, 2
2, 4
...
10, 20
:::
````

:::{table}
labels: $n$, $a_n$
1, 2
2, 4
...
10, 20
:::


### Custom width and alignment

````markdown
:::{table}
---
width: 60%
align: left
---
labels: $x$, $y$
0, 0
1, 1
2, 4
:::
````

:::{table}
---
width: 60%
align: left
---
labels: $x$, $y$
0, 0
1, 1
2, 4
:::



## Tips

- Commas inside math (`$...$`) and quoted strings are preserved — they do not split cells.
- An ellipsis-only row (`...`) produces a $\vdots$ marker in the first column (or the full row when transposed).
- The `width` option accepts CSS units: `%`, `px`, `em`, `rem`, and keywords like `auto` or `fit-content`.

## Source

[`src/munchboka_edutools/directives/table.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/table.py)
