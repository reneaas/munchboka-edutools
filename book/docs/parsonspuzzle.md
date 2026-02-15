# `parsonspuzzle` directive

`parsonspuzzle` is an alias for [`parsons-puzzle`](parsons-puzzle.md).

Creates a Parsons puzzle where learners reorder shuffled code lines.

## Example

````markdown
```{parsonspuzzle} fib-demo
:lang: python

def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
```
````

Use the canonical page for full details: [`parsons-puzzle`](parsons-puzzle.md).
