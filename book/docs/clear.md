# `clear` directive

The `clear` directive inserts a `<div style="clear: both;">` element to clear CSS floats. It forces subsequent content to start below any floated elements rather than wrapping around them.

## Basic usage

````markdown
```{clear}
```
````

## When to use

Use `clear` after floated content (such as sidebar CAS buttons or floated images) to ensure the next block starts on a fresh line:

````markdown
```{cas-popup} 350 500 "CAS" "Calculator"
:layout: sidebar
```

Text that wraps next to the sidebar button...

```{clear}
```

This text starts below the floated button.
````

## Options

This directive has no options and takes no content.

## Source

The implementation lives in `src/munchboka_edutools/directives/clear.py`.
