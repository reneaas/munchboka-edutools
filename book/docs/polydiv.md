# `polydiv` directive

Generates an SVG polynomial long-division layout.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `p` | string (required) |
| `q` | string (required) |
| `stage` | non-negative integer |
| `vars` | string |
| `align` | value |
| `class` | CSS class list |
| `name` | string |
| `cache` | flag |
| `nocache` | flag |
| `alt` | string |
| `width` | length / percentage |
| `inline` | flag |

## Example

````markdown
:::{polydiv}
:p: x^3 - 3x^2 + 1
:q: x - 1
:width: 80%
:::
````

## Source

`src/munchboka_edutools/directives/polydiv.py`
