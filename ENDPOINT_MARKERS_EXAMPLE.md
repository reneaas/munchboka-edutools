# Endpoint Markers Feature - Usage Examples

This document demonstrates the new endpoint markers feature in the plot directive.

## Basic Usage

### Example 1: Closed Endpoints (Included)
```
:::plot
function: sqrt(x), f(x), [0, 4]
endpoint_markers: true
xmin: -1
xmax: 5
ymin: -1
ymax: 3
:::
```

This draws the square root function from 0 to 4 with bracket markers `[` at x=0 and `]` at x=4 to indicate both endpoints are included.

### Example 2: Open Endpoints (Excluded) with Angle Brackets
```
:::plot
function: 1/x, g(x), ⟨-5, 0⟩
endpoint_markers: true
xmin: -6
xmax: 1
ymin: -2
ymax: 2
:::
```

This draws 1/x with angle bracket markers `⟨` at x=-5 and `⟩` at x=0 to indicate open endpoints.

### Example 3: Mixed Endpoints
```
:::plot
function: x**2, h(x), (0, 3]
endpoint_markers: true
xmin: -1
xmax: 4
ymin: -1
ymax: 10
:::
```

This draws x² from 0 (open, no marker at start) to 3 (closed, bracket marker at end).

### Example 4: Multiple Functions with Different Endpoints
```
:::plot
function: sin(x), f(x), [0, 2*pi]
function: cos(x), g(x), ⟨0, 2*pi⟩
endpoint_markers: true
xmin: -1
xmax: 7
ymin: -2
ymax: 2
:::
```

This draws sine with closed endpoints (brackets) and cosine with open endpoints (angle brackets).

### Example 5: Without Endpoint Markers (Default Behavior)
```
:::plot
function: sqrt(x), f(x), [0, 4]
xmin: -1
xmax: 5
ymin: -1
ymax: 3
:::
```

Even though the domain uses `[0, 4]`, no markers are drawn because `endpoint_markers` defaults to `false`.

## Key Points

1. **Enable markers globally**: Set `endpoint_markers: true` to draw markers.
2. **Default is disabled**: Markers are not drawn unless explicitly enabled.
3. **Bracket types**:
   - `[` / `]` → Closed endpoints (included) with bracket markers
   - `(` / `)` → Open endpoints (excluded) with no/angle markers
   - `⟨` / `⟩` → Open endpoints with angle bracket markers
4. **Mixed endpoints**: You can combine different bracket types, e.g., `[a, b)` or `(a, b]`.
5. **Consistent sizing**: Markers scale with figure size to maintain consistent appearance.
6. **Color matching**: Markers use the same color as the function curve.
7. **Smart handling**: Markers are only drawn at finite y-values (NaN endpoints are skipped).

## Technical Details

- Markers are drawn orthogonal to the curve
- Size is fixed at approximately 10 pixels regardless of figure dimensions
- Markers have a slightly thinner line width (0.8× the function line width) for better aesthetics
- Z-order is set to 10 to ensure markers appear on top of grid lines
