# `interactive-code` directive

Creates an interactive code editor/executor block.

## Signature

- Required arguments: `0`
- Optional arguments: `1`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `lang` | string |
| `predict` | flag |

## Example

````markdown
```{interactive-code} intro-example
:lang: python

for i in range(3):
    print(i)
```
````

## Notes

- Use `:predict:` for prediction mode.

## Source

`src/munchboka_edutools/directives/interactive_code.py`
