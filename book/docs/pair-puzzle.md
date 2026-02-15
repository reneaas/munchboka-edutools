# `pair-puzzle` directive

Creates a drag-and-drop matching puzzle from `left : right` pairs.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `class` | CSS class list |

## Example

````markdown
:::{pair-puzzle}
$2+2$ : 4
$3^2$ : 9
$\sin^2(x)+\cos^2(x)$ : 1
:::
````

## Notes

- Aliases: `pairpuzzle`

## Source

`src/munchboka_edutools/directives/pair_puzzle.py`
