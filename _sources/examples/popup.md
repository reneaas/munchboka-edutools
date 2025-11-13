# Popup Examples

This page demonstrates the popup directive and role.

## Popup Directive (Modal Dialog)

Click the button below to open a modal dialog:

```{popup} Click me!
:title: Example Dialog
:width: 600

This is the content of the popup dialog.

You can use **markdown** formatting here.

And even math: $f(x) = x^2 + 2x + 1$

Display math works too:

$$
\int_0^1 x^2 \, dx = \frac{1}{3}
$$
```

## Popup with Custom Button Text

```{popup} Show More Information
:title: Additional Details
:width: 500

Here are some additional details that you can view in this popup.

- Item 1
- Item 2
- Item 3
```

## Popup Role (Inline Tooltip)

You can also use the popup role inline: This is some {popup}`hover text <This content appears in a tooltip>` in a paragraph.

Another example with {popup}`math <The formula is $E = mc^2$>` content.

## Default Popup

If you don't specify options, defaults are used:

```{popup}
This popup uses all default settings:
- Default button text: "Vis mer"
- Default title: "Mer informasjon"
- Default width: 500px
```

## Multiple Popups

You can have multiple popups on the same page:

```{popup} First Popup
:title: Popup 1

Content for the first popup.
```

```{popup} Second Popup
:title: Popup 2

Content for the second popup.
```

```{popup} Third Popup
:title: Popup 3

Content for the third popup.
```
