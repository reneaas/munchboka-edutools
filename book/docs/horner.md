# `horner` directive

Renders a Horner (synthetic division) scheme as SVG.

## Signature

- Required arguments: `0`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `p` | string (required) |
| `x` | string (required) |
| `stage` | non-negative integer |
| `tutor` | flag |
| `align` | value |
| `class` | CSS class list |
| `name` | string |
| `nocache` | flag |
| `alt` | string |
| `width` | length / percentage |

## Example

````markdown
:::{horner}
:p: x^3 + 2x^2 - 3x - 6
:x: 1
:stage: 2
:::
````

## Source

`src/munchboka_edutools/directives/horner.py`
