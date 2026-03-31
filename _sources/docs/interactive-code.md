# `interactive-code` directive

The `interactive-code` directive creates an interactive code editor where students can write and execute code directly in the browser.

## Basic usage

````markdown
```{interactive-code}
:lang: python

for i in range(3):
    print(i)
```
````

```{interactive-code}
:lang: python

for i in range(3):
    print(i)
```

## Prediction mode

Use `:predict:` to ask students to predict the output before running the code:

````markdown
```{interactive-code}
:lang: python
:predict:

x = 5
print(x * 2)
```
````

## Options

| Option | Meaning | Default |
|---|---|---|
| `lang` | Programming language | `python` |
| `predict` | Enable prediction mode — students guess output first | off |

## Tips

- The optional positional argument (e.g. `intro-example`) gives the block a stable ID for cross-referencing.
- Code in the body becomes the initial content of the editor.

## Source

[`src/munchboka_edutools/directives/interactive_code.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/interactive_code.py)
