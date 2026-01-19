# PDF Math Rendering - Technical Details

## Problem

When building PDFs from Jupyter Book sources using the `pdfhtml` builder, LaTeX math expressions (e.g., `$x^2$` or `$$\int f(x) dx$$`) don't render correctly. This is because:

1. **MathJax is JavaScript-based** - It runs in the browser and doesn't work in PDF conversion tools like WeasyPrint
2. **Default config uses MathJax** - Jupyter Book's `_config.yml` typically configures MathJax for HTML output
3. **PDFs need static rendering** - PDF generation requires math to be pre-rendered as images or native LaTeX

## Solution

The `muncho` CLI tool automatically detects PDF builds and injects the necessary configuration to enable proper LaTeX math rendering using Sphinx's `imgmath` extension.

### How It Works

#### 1. Detection Phase

When you run:
```bash
muncho build matematikk_1t --profile print
```

The tool checks if `builder: pdfhtml` is set in the profile configuration.

#### 2. Configuration Injection

If building a PDF, muncho:

1. **Loads your original `_config.yml`**
   ```yaml
   # Your original config
   sphinx:
     config:
       mathjax_path: https://cdn.jsdelivr.net/npm/mathjax@3.2/es5/tex-mml-chtml.js
       mathjax3_config:
         tex:
           macros:
             annotateAbove: ["\\mathrel{\\overset{...}}", 2]
             # ... your custom macros
   ```

2. **Adds imgmath extension**
   ```yaml
   sphinx:
     extra_extensions:
       - sphinx.ext.imgmath  # Added automatically
   ```

3. **Configures imgmath for high-quality output**
   ```yaml
   sphinx:
     config:
       imgmath_image_format: 'svg'      # Vector graphics
       imgmath_font_size: 12            # Readable size
       html_math_renderer: 'imgmath'    # Use imgmath instead of MathJax
   ```

4. **Preserves your custom macros**
   - All your LaTeX macros from `mathjax3_config.tex.macros` are kept
   - They work with imgmath just like they did with MathJax

#### 3. Temporary Config Creation

Muncho creates a temporary config file (e.g., `tmpXXXX_config.yml`) in your book directory with all the modifications.

#### 4. Build Execution

Jupyter Book is called with the temporary config:
```bash
jb build matematikk_1t --builder pdfhtml --config tmpXXXX_config.yml
```

#### 5. Cleanup

After the build completes (success or failure), muncho automatically deletes the temporary config file.

## What Gets Rendered

### Inline Math
```markdown
The equation $E = mc^2$ is Einstein's famous formula.
```
Renders as an inline SVG image with proper alignment.

### Display Math
```markdown
$$
\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}
$$
```
Renders as a centered SVG image with proper spacing.

### Custom Macros
```markdown
Using custom macro: $\annotateAbove{x+1}{add one}$
```
Your custom LaTeX macros work seamlessly in PDF output.

## Requirements

For imgmath to work, you need LaTeX installed on your system:

### macOS
```bash
brew install --cask mactex
```

### Ubuntu/Debian
```bash
sudo apt-get install texlive texlive-latex-extra dvipng
```

### Windows
Download and install [MiKTeX](https://miktex.org/download)

## Verification

To verify LaTeX is installed:
```bash
latex --version
```

## Configuration Options

You can customize imgmath behavior in your profile:

```yaml
# custom_profiles.yml
profiles:
  my_print:
    description: "Custom print profile"
    processors:
      - name: math_rendering
        enabled: true
        settings:
          # MathRenderingProcessor settings
          enhance_equation_numbers: true
    
    build_options:
      builder: pdfhtml
      # Muncho will automatically inject imgmath config
```

## Advanced: Manual Configuration

If you want to configure imgmath manually (without muncho), add to your `_config.yml`:

```yaml
sphinx:
  extra_extensions:
    - sphinx.ext.imgmath
  
  config:
    imgmath_image_format: 'svg'
    imgmath_font_size: 12
    html_math_renderer: 'imgmath'
    
    # Optional: customize LaTeX preamble
    imgmath_latex_preamble: |
      \usepackage{amsmath}
      \usepackage{amssymb}
```

However, using muncho is recommended as it handles this automatically and preserves your existing MathJax configuration for HTML builds.

## Troubleshooting

### Math not rendering in PDF

**Check LaTeX installation:**
```bash
latex --version
dvipng --version  # or dvisvgm --version for SVG
```

**Verify imgmath is working:**
```bash
python -c "from sphinx.ext import imgmath; print('OK')"
```

**Check build output:**
Muncho will show a message when it creates the PDF config:
```
   📝 Created temporary PDF config with LaTeX math rendering
```

### LaTeX errors during build

Check the Jupyter Book build output for LaTeX errors. Common issues:
- Missing LaTeX packages: Install `texlive-latex-extra`
- Complex macros: Simplify or check LaTeX syntax
- Unsupported math environments: Verify they work with basic LaTeX

### Math works in HTML but not PDF

This is expected if you're not using muncho. Use:
```bash
muncho build your_book --profile print
```

instead of:
```bash
jb build your_book --builder pdfhtml
```

## Performance

**SVG vs PNG:**
- SVG (default): Vector graphics, scales perfectly, larger files
- PNG: Raster graphics, fixed resolution, smaller files

Change format if needed:
```yaml
sphinx:
  config:
    imgmath_image_format: 'png'
    imgmath_dvipng_args: ['-gamma', '1.5', '-D', '110', '-bg', 'Transparent']
```

## Comparison: Before vs After

### Before (without muncho)
```bash
jb build matematikk_1t --builder pdfhtml
```
- ❌ Math doesn't render (shows raw LaTeX)
- ❌ MathJax scripts in PDF (useless)
- ❌ Manual config changes needed

### After (with muncho)
```bash
muncho build matematikk_1t --profile print
```
- ✅ Math renders beautifully as SVG
- ✅ Automatic configuration
- ✅ No source file changes needed
- ✅ Custom macros preserved

## References

- [Sphinx imgmath documentation](https://www.sphinx-doc.org/en/master/usage/extensions/math.html#module-sphinx.ext.imgmath)
- [Jupyter Book PDF builds](https://jupyterbook.org/en/stable/advanced/pdf.html)
- [LaTeX installation guide](https://www.latex-project.org/get/)
