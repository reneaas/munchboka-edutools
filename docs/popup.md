# Popup Directive and Role

The `popup` extension provides two ways to add interactive popups to your documentation:

1. **Directive**: Creates a button that opens a modal dialog
2. **Role**: Creates inline text with hover tooltips

## Popup Directive

The popup directive creates a button that, when clicked, opens a modal dialog with your content.

### Basic Usage

````markdown
```{popup} Button Text
Content goes here.
```
````

### Options

- **`:title:`** - Dialog title (default: "Mer informasjon")
- **`:width:`** - Dialog width in pixels (default: 500)
- **`:height:`** - Dialog height in pixels or "auto" (default: "auto")

### Examples

#### Simple Popup

````markdown
```{popup} Click me!
This is a simple popup with default settings.
```
````

#### Popup with Custom Title and Size

````markdown
```{popup} Show Details
:title: Detailed Information
:width: 700
:height: 400

This popup has a custom title and specific dimensions.
```
````

#### Popup with Math Content

````markdown
```{popup} Show Formula
:title: Mathematical Formula

The quadratic formula is:

$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$
```
````

## Popup Role

The popup role creates inline text with a tooltip that appears on hover.

### Usage

```markdown
This is {popup}`hover text <tooltip content>` in a sentence.
```

### Examples

#### Simple Tooltip

```markdown
The {popup}`capital of Norway <Oslo>` is located in the south.
```

#### Math Tooltip

```markdown
Einstein's famous equation is {popup}`E=mc² <Energy equals mass times the speed of light squared: $E = mc^2$>`.
```

## Features

### Automatic Script Loading

The popup directive automatically loads required libraries:
- jQuery (for DOM manipulation)
- jQuery UI (for dialog functionality)
- KaTeX (for math rendering)

Scripts are loaded on-demand and only once per page.

### Math Rendering

Both display and inline math are automatically rendered using KaTeX:

- Inline math: `$x^2$`
- Display math: `$$\int_0^1 x \, dx$$`

### Markdown Support

The popup content supports full MyST markdown syntax:

- **Bold**, *italic*, `code`
- Lists (ordered and unordered)
- Links
- Images
- And more!

### Multiple Popups

You can have as many popups as you need on a single page. Each popup gets a unique ID automatically.

## Styling

The popups use jQuery UI themes for consistent styling. You can customize the appearance by:

1. Overriding the `.popup-button` CSS class for buttons
2. Overriding the `.popup-dialog` CSS class for dialogs
3. Overriding the `.popup-bubble` CSS class for role tooltips

## Technical Details

- **Directive Type**: Custom Sphinx directive
- **Role Type**: Custom Sphinx role
- **Dependencies**: jQuery, jQuery UI, KaTeX
- **Browser Support**: Modern browsers with ES6 support
