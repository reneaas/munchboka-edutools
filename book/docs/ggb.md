# `ggb` directive

Embeds an interactive GeoGebra applet.

## Signature

- Required arguments: `0`
- Optional arguments: `2`
- Body content: `no`

## Options

| Option | Type |
|---|---|
| `material_id` | string |
| `toolbar` | string |
| `menubar` | string |
| `algebra` | string |
| `perspective` | string |

## Example

````markdown
```{ggb} 720 600
:material_id: abcdef123
:toolbar: true
:menubar: false
:algebra: true
```
````

## Source

`src/munchboka_edutools/directives/ggb.py`
