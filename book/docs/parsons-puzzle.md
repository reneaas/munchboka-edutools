# `parsons-puzzle` directive

Creates a Parsons puzzle where learners reorder shuffled code lines.

## Signature

- Required arguments: `0`
- Optional arguments: `1`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `lang` | string |

## Example

````markdown
```{parsons-puzzle} fib-demo
:lang: python

def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
```
````

## Notes

- Aliases: `parsonspuzzle`

## Source

`src/munchboka_edutools/directives/parsons.py`
