# `pair-puzzle` directive

The `pair-puzzle` directive creates a drag-and-drop matching puzzle. Students pair left-side items with their matching right-side items.

## Basic usage

````markdown
:::{pair-puzzle}
$2+2$ : 4
$3^2$ : 9
$\sin^2(x)+\cos^2(x)$ : 1
:::
````

:::{pair-puzzle}
$2+2$ : 4
$3^2$ : 9
$\sin^2(x)+\cos^2(x)$ : 1
:::

## Syntax overview

Each line is a pair separated by ` : ` (space-colon-space):

```
left expression : right expression
```

Both sides support inline math with `$...$`.

## Options

| Option | Meaning | Default |
|---|---|---|
| `class` | Extra CSS classes | — |

## Notes

- Aliases: `pairpuzzle`

## Source

[`src/munchboka_edutools/directives/pair_puzzle.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/pair_puzzle.py)
