# `signchart` directive

Generates a sign chart for a function (original implementation).

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
| `function` | string (required) |
| `factors` | string |
| `xmin` | string |
| `xmax` | string |

## Example

````markdown
```{signchart}
---
function: x**2 - 4, f(x)
factors: true
width: 80%
---
```
````

## Notes

- Aliases: `sign-chart`

## Source

`src/munchboka_edutools/directives/signchart.py`
