# `factor-tree` directive

Generates a factor-tree figure for an integer.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `width` | length / percentage |
| `align` | value |
| `class` | CSS class list |
| `name` | string |
| `nocache` | flag |
| `debug` | flag |
| `alt` | string |
| `n` | string |
| `angle` | string |
| `branch_length` | string |
| `fontsize` | string |
| `figsize` | string |
| `figwidth` | string |
| `figheight` | string |

## Example

````markdown
```{factor-tree}
:n: 84
:width: 70%
```
````

## Source

`src/munchboka_edutools/directives/factor_tree.py`
