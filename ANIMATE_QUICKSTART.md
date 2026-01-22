# Animation Directive - Quick Start Guide

The `animate` directive creates animated plots with transparent backgrounds for web deployment.

## Installation

Ensure you have the required dependencies:

```bash
pip install munchboka-edutools[animations]
# Or manually:
pip install Pillow cairosvg imageio
```

## Basic Usage

### 1. Simplest Animation

```markdown
:::{animate}
animate-var: a, 0, 10, 20
function: sin(a*x)
xmin: -10
xmax: 10
:::
```

This creates a 20-frame animation where variable `a` goes from 0 to 10.

### 2. Common Patterns

**Rotating Vector:**
```markdown
:::{animate}
animate-var: theta, 0, 360, 36
vector: 0, 0, cos(theta*pi/180), sin(theta*pi/180)
:::
```

**Moving Point:**
```markdown
:::{animate}
animate-var: t, -5, 5, 30
function: x**2
point: t, t**2
:::
```

**Changing Parameter:**
```markdown
:::{animate}
animate-var: n, 1, 10, 10
function: x**n
:::
```

### 3. Control Options

```markdown
:::{animate}
animate-var: a, 0, 2*pi, 30
fps: 15                  # Speed (frames per second)
format: webp             # Output format (webp or gif)
loop: true               # Loop infinitely
width: 80%               # Display width

function: sin(a*x)
xmin: -10
xmax: 10
:::
```

## Animation Variable Syntax

```
animate-var: name, start, end, frames
```

- **name**: Variable identifier (e.g., `a`, `t`, `theta`)
- **start**: Starting value (supports expressions: `0`, `pi`, `sqrt(2)`)
- **end**: Ending value (supports expressions: `2*pi`, `10`, `E`)
- **frames**: Number of frames to generate

### Examples:

```markdown
animate-var: t, 0, 2*pi, 30        # 30 frames from 0 to 2π
animate-var: a, -5, 5, 25          # 25 frames from -5 to 5
animate-var: n, 1, 10, 10          # 10 frames from 1 to 10
animate-var: phi, 0, pi/2, 20      # 20 frames from 0 to π/2
```

## All Plot Features Supported

The animate directive supports **all features** from the plot directive:

- Functions: `function: sin(x), cos(x), x**2`
- Points: `point: (x, y)`
- Vectors: `vector: x, y, dx, dy, color`
- Lines: `line: a, b, style, color`
- Circles: `circle: cx, cy, r, style, color`
- Annotations: `annotate: (x1,y1), (x2,y2), text, arc`
- And many more...

## Output Formats

### WebP (Default - Recommended)
```markdown
format: webp
```
- Smaller file size (30-50% smaller than GIF)
- Better quality
- Native transparency
- Modern browser support

### GIF (Universal Compatibility)
```markdown
format: gif
```
- Universal browser support
- Larger file size
- Good transparency support

## Performance Tips

1. **Frame Count**: 20-40 frames is usually sufficient
   ```markdown
   animate-var: a, 0, 10, 30  # Good balance
   ```

2. **FPS**: 8-15 fps is smooth for math animations
   ```markdown
   fps: 10  # Smooth and reasonable file size
   ```

3. **Use WebP**: Smaller files, better quality
   ```markdown
   format: webp
   ```

4. **Cache**: Animations are cached - they only regenerate when content changes

## Common Use Cases

### 1. Parametric Curves
```markdown
:::{animate}
animate-var: t, 0, 2*pi, 40
curve: 2*cos(t), 2*sin(t), (0, 2*pi)
point: 2*cos(t), 2*sin(t)
:::
```

### 2. Function Transformations
```markdown
:::{animate}
animate-var: a, 0.5, 3, 25
function: a*sin(x)
function: sin(x), "Original"
:::
```

### 3. Geometric Animations
```markdown
:::{animate}
animate-var: r, 0.5, 4, 30
circle: 0, 0, r
point: 0, 0
axis: equal
:::
```

### 4. Physics Simulations
```markdown
:::{animate}
animate-var: t, 0, 5, 50
point: t, -0.5*9.81*t**2
vector: t, -0.5*9.81*t**2, 0, -9.81*t, red
:::
```

## Integration with Multi-Plot

Animations work seamlessly in multi-plot layouts:

```markdown
:::::{multi-plot2}
rows: 1
cols: 2

:::{animate}
animate-var: a, 1, 5, 20
function: sin(a*x)
:::

:::{animate}
animate-var: a, 1, 5, 20
function: cos(a*x)
:::
:::::
```

## Troubleshooting

### Animation not generating?
- Check that `animate-var` syntax is correct
- Verify all dependencies are installed: `pip install Pillow cairosvg imageio`
- Check build logs for error messages

### Large file sizes?
- Reduce frame count
- Lower FPS
- Use WebP instead of GIF
- Simplify the plot (fewer elements, lower fontsize)

### Transparency not working?
- Make sure you're using WebP or GIF format
- Verify cairosvg is installed correctly
- Check that your browser supports the format

## Next Steps

- See [animate.md](animate.md) for comprehensive examples
- Check [plot directive docs](../README.md) for all plot features
- Explore mathematical expressions with SymPy

## Example: Complete Animation

```markdown
:::{animate}
animate-var: t, 0, 4, 40
fps: 12
format: webp
loop: true

# Projectile motion
function: -0.5*9.81*x**2 / (10*cos(0.7854))**2 + x*tan(0.7854)
point: 10*cos(0.7854)*t, 10*sin(0.7854)*t - 0.5*9.81*t**2
vector: 10*cos(0.7854)*t, 10*sin(0.7854)*t - 0.5*9.81*t**2, 10*cos(0.7854), 10*sin(0.7854) - 9.81*t, blue

xmin: 0
xmax: 12
ymin: 0
ymax: 6
grid: true
xlabel: $x$ [m]
ylabel: $y$ [m]
width: 90%
:::
Kastebevegelse med utgangsfart 10 m/s i 45° vinkel.
```

This creates a professional physics animation showing projectile motion with trajectory and velocity vector!
