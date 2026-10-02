# `plot-builder` directive

:::{plot-builder}
:::

The `plot-builder` directive embeds a small, fully client-side tool for
composing a 2D figure interactively: set up the coordinate system (axis
ranges and tick spacing), add one or more function graphs, points, and text
labels, then download the result as an SVG file.

It is meant as a scratchpad for *authoring* figures — sketch something here,
then transcribe the ranges/functions/points into a real [`plot`](plot.md)
directive to get the book's actual matplotlib-rendered figure style. The
`plot-builder` preview itself is rendered by the vendored
[JSXGraph](https://jsxgraph.org) library, not matplotlib, so its look (fonts,
line style, tick marks, ...) is only an approximation of what `plot` produces
— the downloaded SVG will **not** look pixel-identical to a `plot` figure.

## Usage

```markdown
:::{plot-builder}
:::
```

The directive takes no required content. Optional options:

- `width` — CSS width of the plotting area (default `640px`, matplotlib's
  default figure width at 100 dpi).
- `height` — pixel height of the plotting area (default `480`, matplotlib's
  default figure height at 100 dpi).
- `name` — used for cross-referencing, same as other directives.

## What you can do in the widget

1. **Coordinate system** — set `xmin`, `xmax`, `ymin`, `ymax`, the tick
   spacing (`x-steg`/`y-steg`), and an optional `x-akse`/`y-akse` label shown
   at the tip of each axis.
2. **Functions** — add one or more rows, each with a color and an expression
   in `x` (e.g. `x^2 - 2*x`, `sin(x)`). Expressions are parsed by JSXGraph's
   own JessieCode engine, so most ordinary math notation works; an invalid
   expression shows an inline error instead of breaking the figure. The
   optional `fra`/`til` fields restrict the graph to a domain `[fra, til]`;
   leave both blank to plot over the whole visible range.
3. **Points** — add `(x, y)` pairs with an optional label.
4. **Text** — place arbitrary text at any `(x, y)` position.
5. **Download as SVG** — grabs the live figure exactly as shown and saves it
   as a `.svg` file.

All labels (axis labels, point labels, free text) are rendered through the
vendored [KaTeX](https://katex.org) engine, so they accept LaTeX math syntax
directly, e.g. `x^2`, `\sqrt{2}`, `\vec{v}`. Wrapping the text in `$...$` (as
in the `plot` directive) also works — the `$` are stripped before rendering.
Downloaded SVGs contain the math labels as vector paths, so symbols, accents,
and subscripts render without external fonts or HTML layout support.

The figure rebuilds automatically a moment after any field changes. Panning
and zooming are disabled on purpose, so the figure always matches exactly the
ranges you typed in — what you see is what gets downloaded.
