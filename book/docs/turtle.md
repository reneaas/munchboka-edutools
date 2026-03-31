# `turtle` directive

The `turtle` directive creates an interactive turtle graphics block where students can write Python turtle code and see the result rendered in the browser.

## Basic usage

````markdown
```{turtle}
from turtle import *
for _ in range(4):
    forward(100)
    right(90)
```
````

```{turtle}
from turtle import *
for _ in range(4):
    forward(100)
    right(90)
```

## Syntax overview

The body contains Python turtle code. Standard turtle commands are supported: `forward()`, `backward()`, `right()`, `left()`, `penup()`, `pendown()`, `color()`, `circle()`, etc.

## Options

| Option | Meaning | Default |
|---|---|---|
| `width` | Canvas width | auto |
| `height` | Canvas height | auto |

## Tips

- The optional positional argument gives the block a stable ID.
- The canvas is rendered in the browser using a JavaScript turtle implementation.

## Source

[`src/munchboka_edutools/directives/turtle.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/turtle.py)
