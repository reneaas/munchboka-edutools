# `exercise` directive

Creates a styled exercise/task admonition.

## Signature

- Required arguments: `1`
- Optional arguments: `0`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `level` | string |

## Example

````markdown
:::{exercise} Practice
Find the derivative of $f(x)=x^3-2x$.
:::
````

## Notes

- Optional `:level:` can be used to tag difficulty.

## Source

`src/munchboka_edutools/directives/admonitions.py`
