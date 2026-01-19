# Muncho Quick Start Guide

This guide will help you get started with the `muncho` CLI tool for building enhanced books.

## Installation

```bash
cd munchboka-edutools
pip install -e .
```

## Basic Usage

### 1. Build with Default Profile

The simplest way to build a book:

```bash
muncho build /path/to/matematikk_1t
```

This will:
1. Run `jupyter-book build` on the book
2. Apply basic typography enhancements
3. Add page break controls
4. Enhance math rendering

### 2. Build for Print (Recommended)

For high-quality print output:

```bash
muncho build matematikk_1t --profile print
```

This profile includes:
- Norwegian smart quotes (« »)
- Proper hyphenation
- Widow and orphan control
- Non-breaking spaces for units
- Optimized page breaks
- Enhanced math typography
- **Automatic LaTeX math rendering for PDF** (uses `imgmath`)

#### How PDF Math Rendering Works

When using the `print` profile (or any profile with `builder: pdfhtml`), muncho automatically:

1. Detects that you're building a PDF
2. Creates a temporary `_config.yml` with LaTeX math rendering enabled
3. Adds `sphinx.ext.imgmath` to render math as SVG images
4. Disables JavaScript-based MathJax (which doesn't work in PDFs)
5. Preserves all your custom LaTeX macros from your original config
6. Cleans up temporary files after the build

**Result:** All math expressions (`$...$` and `$$...$$`) render beautifully in the PDF output!

**No changes needed to your source files** - muncho handles everything automatically.

### 3. Build for Web

For online viewing only:

```bash
muncho build matematikk_r1 --profile web
```

This disables print-specific features.

## Custom Profiles

### Create a Custom Profile

1. Create a `my_profiles.yml` file:

```yaml
profiles:
  my_custom:
    description: "My custom build profile"
    processors:
      - name: typography
        enabled: true
        settings:
          smart_quotes: true
          non_breaking_spaces: true
          number_formatting: true
      
      - name: page_breaks
        enabled: true
      
      - name: math_rendering
        enabled: true
    
    build_options:
      builder: pdfhtml
```

2. Use it:

```bash
muncho build matematikk_1t --config my_profiles.yml --profile my_custom
```

### See Example Profiles

Check out [example_profiles.yml](example_profiles.yml) for more examples.

## Testing Your Book

### Quick Build Test

```bash
# Test with default profile
muncho build matematikk_1t

# Check the output in _build/html/
```

### Compare Profiles

Build with different profiles to compare:

```bash
# Original (no enhancements)
jupyter-book build matematikk_1t

# With enhancements
muncho build matematikk_1t --profile print
```

## Tips & Tricks

### 1. Custom Output Directory

```bash
muncho build matematikk_1t --profile print --output /tmp/test_build
```

### 2. List Available Profiles

```bash
muncho profiles
```

### 3. Preview Processors

```bash
muncho build --list-profiles
```

## Troubleshooting

### Issue: "Profile not found"

**Solution:** List available profiles with `muncho profiles` or specify a config file.

### Issue: Build fails

**Solution:** Try running `jupyter-book build` directly first to see if it's a JupyterBook issue:

```bash
jupyter-book build matematikk_1t
```

### Issue: Output looks different

**Solution:** Processors modify HTML after building. Check the profile settings and disable specific processors if needed.

## Next Steps

- Read [CLI_README.md](CLI_README.md) for full documentation
- Explore processor settings in [example_profiles.yml](example_profiles.yml)
- Create custom processors for your specific needs

## Feedback

If you encounter issues or have suggestions, please open an issue on GitHub or contact the maintainer.
