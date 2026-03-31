# `parsons-puzzle` directive

The `parsons-puzzle` directive creates a Parsons puzzle where learners reorder shuffled code lines into the correct sequence.

## Basic usage

````markdown
```{parsons-puzzle}
:lang: python

def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
```
````

```{parsons-puzzle}
:lang: python

def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
```

## Chunking with `# chunk`

By default each line is a separate draggable block. To create larger blocks, use a marker comment to group lines:

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

Marker lines are **not** included in the final solved code.

You can customize the marker:

````markdown
:::{parsons-puzzle}
:chunk-marker: # chunk

:::{code-block} python
...
:::
:::
````

## Options

| Option | Meaning | Default |
|---|---|---|
| `lang` | Programming language for syntax highlighting | — |
| `chunk-marker` | Custom marker string for chunking | `# chunk` |

## Notes

- Aliases: `parsonspuzzle`

## Source

[`src/munchboka_edutools/directives/parsons.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/parsons.py)
