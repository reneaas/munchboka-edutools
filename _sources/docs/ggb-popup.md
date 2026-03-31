# `ggb-popup` directive

The `ggb-popup` directive creates a button that opens a GeoGebra applet in a modal dialog.

## Basic usage

````markdown
```{ggb-popup} 800 600 "Open GeoGebra" "GeoGebra"
:perspective: AG
:menubar: false
```
````

## Syntax overview

```
```{ggb-popup} <width> <height> <button_text> <dialog_title>
:perspective: <code>
```
```

The four optional positional arguments control the dialog size and button/title text. All are optional and have sensible defaults.

## Options

| Option | Meaning | Default |
|---|---|---|
| `layout` | Layout mode | — |
| `menubar` | Show menu bar in the applet | — |
| `perspective` | GeoGebra perspective code (e.g. `AG`) | — |

## Notes

- Aliases: `ggbpopup`

## Source

[`src/munchboka_edutools/directives/ggb_popup.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/ggb_popup.py)
