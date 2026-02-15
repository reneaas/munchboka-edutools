# `ggb-popup` directive

Creates a button that opens a GeoGebra applet in a dialog.

## Signature

- Required arguments: `0`
- Optional arguments: `4`
- Body content: `no`

## Options

| Option | Type |
|---|---|
| `layout` | value |
| `menubar` | value |
| `perspective` | value |

## Example

````markdown
```{ggb-popup} 800 600 "Open GeoGebra" "GeoGebra"
:perspective: AG
:menubar: false
```
````

## Notes

- Aliases: `ggbpopup`

## Source

`src/munchboka_edutools/directives/ggb_popup.py`
