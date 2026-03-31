# `cas-popup` directive

The `cas-popup` directive creates a button that opens a GeoGebra CAS (Computer Algebra System) window in a resizable, draggable popup dialog. The calculator state is persisted in the browser's local storage.

## Basic usage

A default CAS button with a 350×500 window:

````markdown
```{cas-popup}
```
````

which yields:

```{cas-popup}
```

## Custom size

Specify width and height in pixels:

````markdown
```{cas-popup} 600 700
```
````

which yields:

```{cas-popup} 600 700
```

## Custom button text and title

The third and fourth arguments set the button label and dialog title:

````markdown
```{cas-popup} 500 600 "Open Calculator" "CAS Calculator"
```
````

which yields:

```{cas-popup} 500 600 "Open Calculator" "CAS Calculator"
```

## Sidebar layout

Use `:layout: sidebar` to float the button to the right side:

````markdown
```{cas-popup} 350 500 "CAS" "Calculator"
:layout: sidebar
```
````

## Options

| Option | Meaning |
|---|---|
| `layout` | `sidebar` to float the button right; default is inline |

## Arguments

The directive accepts up to four positional arguments:

| Position | Meaning | Default |
|---|---|---|
| 1 | Width in pixels | `350` |
| 2 | Height in pixels | `500` |
| 3 | Button text | `"Åpne CAS‑vindu"` |
| 4 | Dialog title | `"CAS‑vindu"` |

## Source

The implementation lives in `src/munchboka_edutools/directives/cas_popup.py`.
