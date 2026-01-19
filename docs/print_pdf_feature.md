# Print-Friendly PDF Feature

## Overview

The munchboka-edutools package now includes automatic print-friendly CSS and JavaScript that makes creating clean PDFs from any book page as simple as pressing Ctrl+P.

## What It Does

When a user prints a page (or saves as PDF):

1. **Tab-sets are flattened** - All tabs show sequentially with part labels (a, b, c, etc.)
2. **Answers/solutions hidden** - Clean problem sheets without solutions
3. **Answer key generated** - All answers collected on separate pages at the end
4. **CAS popups hidden** - Interactive buttons removed
5. **Better formatting** - Proper page breaks, exercise grouping, good contrast

## Files

Located in `src/munchboka_edutools/static/`:

- `css/print_pdf.css` - Print-specific CSS rules (@media print)
- `js/print_answer_key.js` - JavaScript to generate answer key

These are automatically registered in `__init__.py` and copied to `_static/munchboka/` during build.

## How It Works

### CSS (`print_pdf.css`)

Uses `@media print` queries to:
- Hide interactive elements (`.dropdown`, `.cas-popup-button`, etc.)
- Show all `.sd-tab-content` elements sequentially
- Hide `.answer` and `.solution` admonitions
- Style the `.answer-key-section`
- Prevent bad page breaks

### JavaScript (`print_answer_key.js`)

Listens for `beforeprint` event and:
1. Collects all `.answer` elements
2. Finds parent `.exercise` for each
3. Identifies tab parts (a, b, c)
4. Creates formatted answer key HTML
5. Appends to end of document
6. Cleans up on `afterprint`

## Integration

Books using munchboka-edutools automatically get this feature. No configuration needed!

Simply add to `_config.yml`:
```yaml
sphinx:
  extra_extensions:
    - munchboka_edutools
```

## Usage

**Students:**
1. Open any chapter
2. Press Ctrl+P (or Cmd+P)
3. Select "Save as PDF"
4. Done!

**Teachers:**
Can customize behavior by editing `print_pdf.css` (e.g., show answers inline instead of at end).

## Documentation

Full documentation: [docs/print_pdf.md](print_pdf.md)

## Benefits

- **Simple:** One-click PDF creation
- **Fast:** Browser rendering, no build process
- **Flexible:** Easy CSS/JS customization
- **Universal:** Works in all modern browsers
- **No dependencies:** Just needs the browser
- **Per-page PDFs:** Any page, anytime

## Browser Compatibility

| Browser | Tab Flattening | Answer Key | Page Breaks |
|---------|---------------|------------|-------------|
| Chrome  | ✅            | ✅         | ✅          |
| Firefox | ✅            | ✅         | ⚠️          |
| Safari  | ✅            | ✅         | ✅          |
| Edge    | ✅            | ✅         | ✅          |

Note: Firefox has limited CSS page-break support, but core functionality works.

## Maintenance

To update print behavior:
1. Edit `src/munchboka_edutools/static/css/print_pdf.css` (CSS rules)
2. Edit `src/munchboka_edutools/static/js/print_answer_key.js` (JavaScript logic)
3. Rebuild package: `pip install -e .`
4. Books will get updates on next build

## Future Enhancements

Potential improvements:
- Chapter-specific answer keys
- QR codes to online solutions
- Difficulty indicators
- Time estimates
- Teacher/student mode toggle
- Batch PDF generation script
