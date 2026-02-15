# `popup` directive

Creates a button-triggered modal popup dialog.

## Signature

- Required arguments: `0`
- Optional arguments: `1`
- Body content: `yes`

## Options

| Option | Type |
|---|---|
| `title` | string |
| `width` | positive integer |
| `height` | string |

## Example

````markdown
```{popup} Show details
:title: Extra information
:width: 500

This content appears inside the modal.
```
````

## Notes

- This module also registers the inline role `{popup}` for tooltip-like content.

## Source

`src/munchboka_edutools/directives/popup.py`
