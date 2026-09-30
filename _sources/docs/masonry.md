# Masonry cards

`masonry` arranges cards in independent columns. Each card keeps its natural
height, so another card can fit below a short card beside a taller one.
No Sphinx Design dependency is required.

## Example

::::{masonry}
:columns: 1 2 3
:gap: 1rem

:::{masonry-card} Short explanation
A short paragraph.
:::

:::{masonry-card} Worked example
This card contains more content and keeps its natural height.

For a quadratic function,

$$f(x) = ax^2 + bx + c,$$

the axis of symmetry is $x = -b/(2a)$.

1. Identify the coefficients.
2. Find the axis of symmetry.
3. Evaluate the function there.
:::

:::{masonry-card} Exercise
Find the minimum of $f(x) = x^2 - 4x + 3$.
:::

:::{masonry-card} Hint
Complete the square.
:::

::::

## MyST syntax

`````markdown
::::{masonry}
:columns: 1 2 3
:gap: 1rem
:placement: shortest

:::{masonry-card} Short explanation
A short paragraph.
:::

:::{masonry-card} Worked example
Longer content, including equations, figures or nested directives.
:::

:::{masonry-card} Exercise
Another card can fit below the shorter explanation.
:::

::::
`````

Enable MyST's `colon_fence` extension to use colon fences. Backtick fences also
work. With reStructuredText, use normal directive nesting:

```rst
.. masonry::
   :columns: 1 2 3
   :gap: 1rem

   .. masonry-card:: Short explanation

      A short paragraph.

   .. masonry-card:: Worked example

      Longer content.
```

## Options

| Directive | Option | Default | Meaning |
| --- | --- | --- | --- |
| `masonry` | `columns` | `1 2 3` | One fixed count, or three counts for container widths below 600px, from 600px to below 900px, and at least 900px. Each count must be 1–12. |
| `masonry` | `gap` | `1rem` | Nonnegative spacing in `px`, `rem` or `em`, or `0`. |
| `masonry` | `placement` | `shortest` | `shortest` fills the shortest column next; ties follow reading direction. `alternating` assigns successive cards to successive columns, independently stacking each column. |
| Both | `class` | — | Additional CSS classes. |
| Both | `name` | — | A reference target. |

`masonry-card` takes an optional title argument and ordinary document content.
Only `masonry-card` directives can be direct children of `masonry`; put paragraphs,
figures, equations and nested directives inside a card. Cards occupy one column.
A card can also be used on its own.

The layout responds to its container width, including inside admonitions, and
updates when images load, mathematics renders or expandable content changes
height. With the default columns, narrow containers show one column. A fixed
count (for example `:columns: 3`) applies even to narrow containers.

HTML and keyboard order always follow source order; visual placement varies with
card heights. Keep explicit numbering for sequential exercises. Without JavaScript
(or ResizeObserver support), cards form a vertical stack. Printing and non-HTML
builders use ordinary source-order flow.

The directives are automatically available through `munchboka_edutools`. They can
also be loaded independently as `munchboka_edutools.directives.masonry`.
