# `popup` directive

The `popup` directive creates a button that opens a modal popup dialog with arbitrary content.

## Basic usage

````markdown
```{popup} Show details
:title: Extra information
:width: 500

This content appears inside the modal.
```
````

```{popup} Show details
:title: Extra information
:width: 500

This content appears inside the modal.
```

## Syntax overview

The optional positional argument sets the button text. The body content is displayed inside the modal dialog.

## Options

| Option | Meaning | Default |
|---|---|---|
| `title` | Title displayed in the modal header | button text |
| `width` | Modal width in pixels | auto |
| `height` | Modal height | auto |

## Inline role

This module also registers the `{popup}` inline role for tooltip-like popups within running text.

## Source

[`src/munchboka_edutools/directives/popup.py`](https://github.com/reneaas/munchboka-edutools/blob/main/src/munchboka_edutools/directives/popup.py)
