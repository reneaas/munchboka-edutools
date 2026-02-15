# `answer` directive

Creates an admonition block for short answers (collapsed by default).

## Signature

- Required arguments: `0`
- Optional arguments: `1`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `dropdown` | string |

## Example

````markdown
:::{answer}
The solution is $x=4$.
:::
````

## Notes

- Use `:dropdown: 0` to show the content expanded by default.

## Source

`src/munchboka_edutools/directives/admonitions.py`
