# Polynomial Icon Role

The `poly-icon` role displays inline icons representing different polynomial function shapes. This is useful for mathematical content where you need to refer to the shape or behavior of polynomial functions visually.

## Available Icons

The following polynomial icons are available:

### Cubic Functions

Standard cubic function (goes up): {poly-icon}`cubicup`

Negative cubic function (goes down): {poly-icon}`cubicdown`

### Quadratic Functions

Positive quadratic (parabola opening up, "smile"): {poly-icon}`smile`

Negative quadratic (parabola opening down, "frown"): {poly-icon}`frown`

## Usage Examples

### In Text

When analyzing a cubic function {poly-icon}`cubicup`, we notice that it has an S-shaped curve with one turning point. In contrast, a negative cubic {poly-icon}`cubicdown` has the opposite orientation.

For quadratic functions, a positive leading coefficient gives us a {poly-icon}`smile` shape (opening upward), while a negative leading coefficient creates a {poly-icon}`frown` shape (opening downward).

### In Lists

The main types of polynomial shapes:
- Cubic up: {poly-icon}`cubicup`
- Cubic down: {poly-icon}`cubicdown`
- Smile (positive quadratic): {poly-icon}`smile`
- Frown (negative quadratic): {poly-icon}`frown`

### In Tables

| Function Type | Shape | Leading Coefficient |
|--------------|-------|---------------------|
| Standard cubic | {poly-icon}`cubicup` | Positive |
| Negative cubic | {poly-icon}`cubicdown` | Negative |
| Positive quadratic | {poly-icon}`smile` | Positive |
| Negative quadratic | {poly-icon}`frown` | Negative |

## Features

- **Inline display**: Icons appear inline with text
- **Theme-aware**: Automatically adapts to light/dark mode
- **Consistent sizing**: Fixed width (35px) with proper scaling
- **Accessibility**: Alt text describes each icon

## Syntax

```markdown
{poly-icon}`iconname`
```

Where `iconname` is one of:
- `cubicup`
- `cubicdown`
- `smile`
- `frown`
