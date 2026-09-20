# `popup-code` directive

Open an `interactive-code` Python editor in a draggable, resizable window.
Students can keep reading the page while the window is open, close it with
the close button or Escape, and reopen it without losing code or output.
Drag the title bar to move the window (mouse, touch, or pen).

## Basic usage

````markdown
```{popup-code}
for i in range(3):
    print(i)
```
````

```{popup-code}
for i in range(3):
    print(i)
```

An empty body opens a blank editor. Run, reset, cancel, and Python output
work just as in `interactive-code`.

## Size, labels, and sidebar placement

Like `cas-popup`, the arguments are width, height, quoted button text,
and quoted window title. Dimensions include the title bar and are limited
to the available viewport.

````markdown
```{popup-code} 750 600 "Prøv koden" "Python"
:name: loop-practice
:layout: sidebar

for n in range(1, 6):
    print(n**2)
```
````

Alternatively, use options:

```{popup-code}
:width: 750
:height: 600
:button-text: Prøv koden
:title: Python
:name: popup-code-example

print("Hei!")
```

## Options

| Option | Meaning | Default |
|---|---|---|
| `width` | Initial window width in pixels | `500` |
| `height` | Initial window height in pixels | `550` |
| `button-text` | Launcher label | `Åpne kodevindu` |
| `title` | Window title | `Kodevindu` |
| `layout` | `inline` or `sidebar` | `inline` |
| `name` | Unique, stable editor name within this page | Generated |
| `lang` | Language; currently only `python` | `python` |
| `predict` | Ask students to predict output first, as in `interactive-code` | Off |

Options override positional arguments. Use distinct `name` values on the
same page to preserve saved code across rebuilds. The existing editor saves
code in the browser's local storage; output and window placement are retained
only while the page remains loaded.

The directive is registered by `munchboka_edutools`. It can also be enabled
individually as `munchboka_edutools.directives.popup_code`.
