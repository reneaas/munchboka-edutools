# `signchart-2` directive

Generates an enhanced sign chart with broader function support.

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
| `domain` | string |
| `color` | string |
| `generic_labels` | string |
| `small_figsize` | string |
| `figsize` | string |
| `fontsize` | string |
| `labelpad` | string |

## Example

````markdown
```{signchart-2}
---
function: sin(x)*cos(x), f(x)
domain: (-3.5, 3.5)
factors: true
width: 100%
---
```
````

## Notes

- Aliases: `signchart2`

## Source

`src/munchboka_edutools/directives/signchart2.py`
