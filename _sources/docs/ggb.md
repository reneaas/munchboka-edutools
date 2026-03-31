# `ggb` directive

The `ggb` directive embeds an interactive GeoGebra applet directly in the page.

## Basic usage

````markdown
```{ggb} 720 600
:material_id: abcdef123
:toolbar: true
:menubar: false
:algebra: true
```
````

## Syntax overview

```
```{ggb} <width> <height>
:material_id: <GeoGebra material ID>
```
```

The two optional positional arguments set the applet width and height in pixels. The `material_id` specifies which GeoGebra resource to load (the ID from the GeoGebra sharing URL).

## Options

| Option | Meaning | Default |
|---|---|---|
| `material_id` | GeoGebra material ID | — |
| `toolbar` | Show the GeoGebra toolbar | — |
| `menubar` | Show the menu bar | — |
| `algebra` | Show the algebra view | — |
| `perspective` | GeoGebra perspective code (e.g. `AG` for algebra + graphics) | — |

## Source

[`src/munchboka_edutools/directives/ggb.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/ggb.py)
