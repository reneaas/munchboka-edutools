# Muncho - Enhanced Book Builder

Command-line tool for building beautiful, print-ready books from Jupyter Book sources with opinionated formatting rules and typography enhancements.

## Installation

```bash
cd munchboka-edutools
pip install -e .
```

## Quick Start

```bash
# Build with default profile
muncho build matematikk_1t

# Build with print profile (optimized for PDF)
muncho build matematikk_1t --profile print

# Build with web profile (optimized for online viewing)
muncho build matematikk_r1 --profile web

# List available profiles
muncho profiles
```

## Features

### Built-in Processors

1. **Typography Processor** - Print-quality text formatting
   - Norwegian hyphenation hints
   - Widow and orphan control
   - Smart quotes and dashes
   - Non-breaking spaces
   - Number formatting with proper separators

2. **Page Break Processor** - Optimal print layout
   - Force page breaks before chapters
   - Avoid breaks after headings
   - Keep figures and tables together
   - Prevent orphaned content

3. **Math Rendering Processor** - Enhanced mathematical typesetting
   - **PDF Support**: Automatically configures LaTeX math rendering (imgmath) for PDF output
   - **HTML Support**: Optimized MathJax/KaTeX for web viewing
   - Page break protection for equations
   - Improved equation numbering
   - Proper font sizes

## PDF Math Rendering

When building PDFs (`--profile print` or `builder: pdfhtml`), Muncho automatically:

1. Creates a temporary config with `sphinx.ext.imgmath` enabled
2. Configures SVG-based math rendering for high-quality output
3. Disables JavaScript-based MathJax (which doesn't work in PDF)
4. Preserves all your custom LaTeX macros from `_config.yml`

This ensures that all LaTeX math expressions render correctly in the final PDF, without requiring any changes to your source files.

## Profiles

### Built-in Profiles

- **default** - Basic enhancements suitable for most use cases
- **print** - Optimized for high-quality print output (PDF)
- **web** - Optimized for web viewing (HTML)

### Custom Profiles

Create a `profiles.yml` file:

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
      
      - name: page_breaks
        enabled: true
        settings:
          break_before_chapters: true
      
      - name: math_rendering
        enabled: true
    
    build_options:
      builder: pdfhtml
```

Then use it:

```bash
muncho build my_book --config profiles.yml --profile my_custom
```

## Architecture

### Plugin-Based Design

Muncho uses a plugin architecture with processors that transform HTML output:

```
Jupyter Book → HTML → Processor Pipeline → Enhanced HTML → PDF
```

### Processor Priority

Processors run in priority order (lower numbers first):
- **0-10**: Pre-processing (structure modifications)
- **10-50**: Content transformations (typography, math)
- **50-90**: Styling and layout (page breaks)
- **90-100**: Post-processing (cleanup, validation)

### Extending Muncho

Create custom processors by inheriting from `Processor`:

```python
from munchboka_edutools.processors.base import Processor
from bs4 import BeautifulSoup

class MyCustomProcessor(Processor):
    @property
    def name(self) -> str:
        return "my_custom"
    
    @property
    def priority(self) -> int:
        return 40
    
    def process(self, html_content: str, soup: BeautifulSoup, context: dict) -> str:
        # Your custom transformations here
        return str(soup)
```

Register it in `cli/build.py`:

```python
PROCESSOR_CLASSES = {
    "typography": TypographyProcessor,
    "page_breaks": PageBreakProcessor,
    "math_rendering": MathRenderingProcessor,
    "my_custom": MyCustomProcessor,  # Add here
}
```

## CLI Reference

### `muncho build`

Build a book with enhanced formatting.

**Arguments:**
- `BOOK_PATH` - Path to the book directory

**Options:**
- `--profile, -p` - Build profile to use (default: default)
- `--output, -o` - Custom output directory
- `--config, -c` - Path to custom profiles configuration
- `--list-profiles` - List available profiles and exit

**Examples:**

```bash
# Basic build
muncho build matematikk_1t

# Custom output directory
muncho build matematikk_1t --output /tmp/my_output

# Use custom profile
muncho build matematikk_1t --config custom.yml --profile advanced
```

### `muncho profiles`

List all available build profiles with descriptions and enabled processors.

```bash
muncho profiles
```

## Development

### Project Structure

```
munchboka_edutools/
├── cli/
│   ├── __init__.py
│   └── build.py          # Main CLI commands
├── processors/
│   ├── __init__.py
│   ├── base.py           # Base processor class
│   ├── typography.py     # Typography enhancements
│   ├── page_breaks.py    # Page break control
│   └── math_rendering.py # Math typesetting
└── config/
    ├── __init__.py
    └── profiles.py       # Profile management
```

### Adding New Processors

1. Create a new file in `processors/`
2. Inherit from `Processor` base class
3. Implement required methods (`name`, `priority`, `process`)
4. Register in `PROCESSOR_CLASSES` dict
5. Add to profile configurations

### Testing

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/
```

## Roadmap

Planned features:
- [ ] Image optimization processor
- [ ] Table of contents enhancement
- [ ] Cross-reference styling
- [ ] Code block formatting
- [ ] PDF generation with WeasyPrint
- [ ] Incremental builds
- [ ] Watch mode for development

## License

MIT License - See LICENSE file for details
