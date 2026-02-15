# `turtle` directive

Creates an interactive turtle graphics coding block.

## Signature

- Required arguments: `0`
- Optional arguments: `1`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `width` | string |
| `height` | string |

## Example

````markdown
```{turtle}
from turtle import *
for _ in range(4):
    forward(100)
    right(90)
```
````

## Source

`src/munchboka_edutools/directives/turtle.py`
