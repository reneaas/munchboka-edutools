# GeoGebra Applet Examples

This page demonstrates the `{ggb}` directive for embedding interactive GeoGebra applets.

## Example 1: Empty Applet (Full Controls)

When no `material_id` is provided, an empty applet is created with all controls enabled by default:

```{ggb} 800 500
```

## Example 2: Specific GeoGebra Material

You can embed existing GeoGebra materials using their material ID:

```{ggb} 720 600
---
material_id: gt63unet
---
```

## Usage Guide

### Basic Syntax

The `{ggb}` directive accepts two optional positional arguments for dimensions:

```markdown
\`\`\`{ggb} WIDTH HEIGHT
:option: value
\`\`\`
```

### Available Options

- **material_id**: GeoGebra material ID (find at geogebra.org)
  - Example: `:material_id: qzjdaufa`
  
- **toolbar**: Show toolbar (`true`/`false`)
  - Default: `false` (unless no material_id is provided)
  
- **menubar**: Show menubar (`true`/`false`)
  - Default: `false` (unless no material_id is provided)
  
- **algebra**: Show algebra view (`true`/`false`)
  - Default: `false` (unless no material_id is provided)
  
- **perspective**: Set initial perspective
  - Values: `graphing`, `geometry`, `3d`, `spreadsheet`, `cas`, `probability`

### Default Behavior

- If **no material_id** is provided → Empty applet with all controls enabled
- If **material_id** is provided → Minimal controls (toolbar, menubar, algebra all false by default)
- Default dimensions: 720×600 pixels

### Features

All applets include:
- ✅ Fullscreen button
- ✅ Reset icon
- ✅ Norwegian language interface
- ✅ Automatic scaling and responsiveness
