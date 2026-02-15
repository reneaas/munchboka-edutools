# `cas-popup` directive

Creates a button that opens a GeoGebra CAS dialog.

## Signature

- Required arguments: `0`
- Optional arguments: `4`
- Body content: `no`

## Options

| Option | Type |
|---|---|
| `layout` | value |

## Example

````markdown
```{cas-popup} 450 600 "Open CAS" "CAS window"
:layout: sidebar
```
````

## Source

`src/munchboka_edutools/directives/cas_popup.py`
