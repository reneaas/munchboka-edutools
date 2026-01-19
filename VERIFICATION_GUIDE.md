# Quick Verification Guide

This guide helps you verify that PDF math rendering is working correctly in your environment.

## Prerequisites Check

### 1. Verify LaTeX Installation

```bash
# Check if LaTeX is installed
latex --version

# Check if dvisvgm is available (needed for SVG output)
dvisvgm --version

# Check if dvipng is available (alternative for PNG output)
dvipng --version
```

**Expected output:**
```
latex --version
pdfTeX 3.141592653-2.6-1.40.XX (TeX Live 20XX)
```

If you see "command not found", install LaTeX:

**macOS:**
```bash
brew install --cask mactex
```

**Ubuntu/Debian:**
```bash
sudo apt-get install texlive texlive-latex-extra dvipng
```

### 2. Verify muncho Installation

```bash
muncho --version
```

### 3. Verify Sphinx imgmath

```bash
python -c "from sphinx.ext import imgmath; print('imgmath available ✅')"
```

## Quick Test

### Option 1: Using Existing Book

If you have matematikk_1t or matematikk_r1:

```bash
# Navigate to munchboka-edutools
cd /path/to/munchboka-edutools

# Build PDF
muncho build ../matematikk_1t --profile print

# Check for math rendering indicator in output
# You should see:
#    📝 Created temporary PDF config with LaTeX math rendering
```

### Option 2: Using Test Book

If you have the example book in munchboka-edutools:

```bash
cd /path/to/munchboka-edutools

# Build the example book
muncho build book --profile print

# Check output
ls -lh book/_build/pdf/book.pdf
```

## Verify Math in Output

### Check the PDF

1. Open the generated PDF: `book/_build/pdf/book.pdf`
2. Find a page with math equations
3. Verify that:
   - Inline math (like $x^2$) appears correctly
   - Display math (like $$\int f(x)dx$$) is centered and clear
   - Math looks crisp (SVG quality)
   - Custom macros render correctly

### What Good Math Looks Like

✅ **Correct:**
- Equations are crisp and clear
- Symbols are properly formatted
- Fractions, integrals, etc. look professional
- Math inline with text has proper alignment
- Display equations are centered

❌ **Incorrect (if you see these, something is wrong):**
- Raw LaTeX code (e.g., `$x^2$` appearing as text)
- Pixelated or blurry math
- Math overflowing page margins
- JavaScript errors or warnings

## Test with Custom Math

### Create a Test Page

Create `test_math.md` in your book:

```markdown
# Math Test Page

## Inline Math

The quadratic formula is $x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}$.

## Display Math

$$
\int_0^1 x^2 \, dx = \frac{1}{3}
$$

## Custom Macros (if you have them)

Using $\natural$ for natural numbers: $x \in \natural$.

## Complex Expression

$$
\sum_{n=1}^{\infty} \frac{1}{n^2} = \frac{\pi^2}{6}
$$
```

Add to `_toc.yml`:
```yaml
- file: test_math
```

Build and verify:
```bash
muncho build your_book --profile print
```

## Troubleshooting

### Math Not Rendering

**Check build output:**
```bash
muncho build your_book --profile print 2>&1 | grep -A5 -B5 "math\|imgmath"
```

Look for:
- ✅ `Created temporary PDF config with LaTeX math rendering`
- ❌ LaTeX errors or warnings

**Check temporary config (if it wasn't deleted):**
```bash
# List any leftover config files
ls -la your_book/tmp*_config.yml
```

**Test LaTeX directly:**
```bash
# Create a simple LaTeX file
cat > test.tex << 'EOF'
\documentclass{article}
\usepackage{amsmath}
\begin{document}
$E = mc^2$
\end{document}
EOF

# Compile it
latex test.tex
# If this fails, your LaTeX installation has issues
```

### Slow Build Times

LaTeX compilation can be slow for books with many equations. This is normal.

**Tips:**
- First build is slowest (LaTeX packages download)
- Subsequent builds reuse cached fonts
- Consider using PNG instead of SVG for faster builds (trade-off: quality)

### LaTeX Package Errors

If you see errors like `! LaTeX Error: File 'xxx.sty' not found.`

**Install missing packages:**

**macOS (TeX Live):**
```bash
sudo tlmgr install <package-name>
```

**Ubuntu/Debian:**
```bash
sudo apt-get install texlive-latex-extra texlive-fonts-extra
```

## Advanced Verification

### Check Generated Config

To see what muncho generates, modify the cleanup in `build.py` temporarily:

```python
# In _run_jupyter_book_build, comment out cleanup:
# if config_file and config_file.exists():
#     config_file.unlink()
```

Then build and inspect:
```bash
muncho build your_book --profile print
cat your_book/tmp*_config.yml | grep -A10 imgmath
```

You should see:
```yaml
imgmath_image_format: svg
imgmath_font_size: 12
html_math_renderer: imgmath
```

### Test Script

Use the provided test script:
```bash
cd munchboka-edutools
python test_pdf_math.py
```

Expected output:
```
============================================================
Testing PDF Math Rendering Implementation
============================================================

🧪 Testing profile configuration...
✓ Print profile uses pdfhtml builder
✓ Math rendering processor is enabled in print profile

🧪 Testing PDF config generation...
✓ Loaded print profile: Optimized for high-quality print output
✓ Builder: pdfhtml
✓ Using test book: matematikk_1t
✓ BookBuilder initialized successfully
   📝 Created temporary PDF config with LaTeX math rendering
✓ Temporary config created: /path/to/tmpXXXX_config.yml
✓ Config contains correct imgmath settings
✓ Original mathjax3_config preserved
✓ Temporary config cleaned up

============================================================
✅ All tests passed!
```

## Success Checklist

- [ ] LaTeX installed and working (`latex --version`)
- [ ] muncho installed (`muncho --version`)
- [ ] Can build with print profile (`muncho build book --profile print`)
- [ ] See "Created temporary PDF config" message
- [ ] PDF generated successfully
- [ ] Math equations render clearly in PDF
- [ ] Custom macros work (if applicable)
- [ ] Test script passes (`python test_pdf_math.py`)

## Need Help?

If you're still having issues:

1. **Check LaTeX installation:** This is the most common issue
2. **Verify Python environment:** Make sure munchboka-edutools is installed
3. **Look at build logs:** Save full output with `muncho build book --profile print > build.log 2>&1`
4. **Test with simple math:** Start with basic `$x^2$` before complex equations
5. **Check Sphinx version:** `pip show sphinx` (requires >= 6.0)

## Resources

- [Main Documentation](README.md)
- [Technical Details](docs/pdf_math_rendering.md)
- [Implementation Summary](PDF_MATH_IMPLEMENTATION.md)
- [Sphinx imgmath docs](https://www.sphinx-doc.org/en/master/usage/extensions/math.html#module-sphinx.ext.imgmath)
