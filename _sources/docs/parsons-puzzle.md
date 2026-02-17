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

## Chunking with `# chunk`

If you want fewer (larger) draggable blocks, you can separate code into chunks
using a marker comment line. Marker lines are **not** included in the final
solved code (so they won't appear when the solution is injected into
`interactive-code`).

````markdown
:::{parsons-puzzle}
:::{code-block} python
s = 0
# chunk
for i in range(5):
    s += i
# chunk
print(s)
:::
:::
````

You can also override the marker:

````markdown
:::{parsons-puzzle}
:chunk-marker: # chunk

:::{code-block} python
...
:::
:::
````

## Notes

- Aliases: `parsonspuzzle`

## Source

`src/munchboka_edutools/directives/parsons.py`
