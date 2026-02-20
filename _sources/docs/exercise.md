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
| `aids` | boolean (`true`/`false`) |

## Example

````markdown
:::{exercise} Practice
Find the derivative of $f(x)=x^3-2x$.
:::
````

Digital aids example:

````markdown
:::{exercise} Practice (digital aids allowed)
---
aids: true
---

Use a CAS/graphing tool to investigate the function.
:::
````

## Notes

- Optional `:level:` can be used to tag difficulty.
- Use `aids: true` to switch the exercise icon to a computer.

## Source

`src/munchboka_edutools/directives/admonitions.py`
