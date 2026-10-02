# `free-body-diagram-builder` directive

:::{free-body-diagram-builder}
:::

The `free-body-diagram-builder` directive embeds a small, fully client-side
tool for sketching a [`free-body-diagram`](free-body-diagram.md)-style figure
interactively: configure an object, an optional velocity, and one or more
forces — using the same kinds and defaults as the real directive — then
download the result as an SVG file.

It is meant as a scratchpad for *authoring* diagrams — sketch something here,
then transcribe the object/velocity/force lines into a real
[`free-body-diagram`](free-body-diagram.md) directive to get the book's
actual matplotlib-rendered figure style. The preview here is rendered by the
vendored [JSXGraph](https://jsxgraph.org) library, not matplotlib, so its
look is only an approximation — the downloaded SVG will **not** look
pixel-identical to a `free-body-diagram` figure.

## Usage

```markdown
:::{free-body-diagram-builder}
:::
```

The directive takes no required content. Optional options:

- `width` — CSS width of the plotting area (default `640px`).
- `height` — pixel height of the plotting area (default `480`).
- `name` — used for cross-referencing, same as other directives.

## What you can do in the widget

1. **Objekt** — choose a kind (`ball`, `square`/kloss, `toy-car`/bil), its
   size, center position, color, and opacity.
2. **Hastighet** — an optional direction (degrees from +x). Only matters for
   forces whose default direction depends on motion (`friction`,
   `air-resistance`); leave it blank if the object is at rest.
3. **Krefter** — add one or more forces by kind (`gravity`, `normal`,
   `friction`, `air-resistance`, `custom`), with a length, color, and
   optional name. Each kind has the same default attachment point/direction
   and default color/name as the real directive. Open **Avansert** on a row
   to override the attachment point, direction (degrees), or the
   collinear-force offset — the same escape hatches the real directive
   supports. `custom` always requires an explicit point and direction.
4. **Akseindikator** — toggle the small corner x/y arrows.
5. **Download as SVG**.

The builder starts with gravity only. Use **+ Legg til kraft** to add other
forces. Every force starts with an offset of `0`; change it under **Avansert**
to separate overlapping arrows, or clear it to enable automatic spacing.

Default force names use vector notation (e.g. `$\vec G$`). Downloaded SVGs
render the math labels as vector paths, including accents and subscripts.

Like the real directive, every force's true point of attack is marked with a
dot; offset forces have a thin dotted leader back to that point.
All labels (force names, axis indicator)
support LaTeX via the vendored KaTeX engine, same as
[`plot-builder`](plot-builder.md).
