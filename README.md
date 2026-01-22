# munchboka-edutools

Reusable Sphinx / Jupyter Book directives and assets for Norwegian educational content.

**NEW**: Includes `muncho` - a command-line tool for building beautiful, print-ready books with enhanced typography, layout, and **automatic LaTeX math rendering for PDFs**. See [CLI_README.md](CLI_README.md) for details.

## Key Features

✨ **Auto-configured Sphinx extensions** for Jupyter Book  
📚 **Custom educational directives** (quiz, dialogue, plots, animations, etc.)  
🖨️ **Print-optimized PDF builds** with proper typography  
🧮 **Automatic PDF math rendering** - LaTeX expressions work seamlessly in PDFs  
🎨 **Multiple build profiles** (print, web, custom)  
🎬 **Animated plots** - Create animations with transparent backgrounds (WebP/GIF)  
📄 **Print-friendly CSS** - Browser "Print to PDF" creates clean problem sheets with answer keys

## Install

```bash
pip install munchboka-edutools
```

## Usage

### As Sphinx Extensions (Jupyter Book `_config.yml`)

```yaml
sphinx:
  extra_extensions:
    - munchboka_edutools
```

All packaged directives are auto-registered. Static assets (including print-friendly CSS and JS) are placed under `_static/munchboka/` during the build.

### Print-Friendly PDFs

Simply press **Ctrl+P** (or Cmd+P) in your browser when viewing any page to create a clean PDF with:
- All tabs flattened with part labels (a, b, c, etc.)
- Answers and solutions hidden from main content
- Automatic answer key page at the end
- CAS popup buttons hidden
- Better page breaks

See [docs/print_pdf.md](docs/print_pdf.md) for details.

### As Build Tool

Build books with enhanced formatting:

```bash
# Print-optimized build (includes automatic PDF math rendering)
muncho build matematikk_1t --profile print

# Web-optimized build
muncho build matematikk_r1 --profile web

# See all options
muncho --help
```

**PDF Math Rendering**: When building PDFs, muncho automatically configures `sphinx.ext.imgmath` to render LaTeX math expressions as high-quality SVG images. No changes to your source files needed!

See [CLI_README.md](CLI_README.md) for full CLI documentation and [QUICKSTART.md](QUICKSTART.md) for a quick start guide.

## Development

Clone and install dev extras:

```bash
pip install -e .[dev]
```

### Local demo book

Build the embedded demo book:

```bash
jupyter-book build book/
```

### Adding a new directive

1. Create `src/munchboka_edutools/directives/my_directive.py` exposing `setup(app)`.
2. The package auto-loads modules under `munchboka_edutools.directives`.
3. Add an example page in `book/examples/`.

### Testing

Run tests:

```bash
pytest -q
```

## Quick Links

- **[Animation Quickstart](ANIMATE_QUICKSTART.md)** - Create animated plots
- **[CLI Documentation](CLI_README.md)** - Build tool guide
- **[Quick Start](QUICKSTART.md)** - Get started quickly
- **[Print PDF Guide](docs/print_pdf.md)** - Browser printing features
- **[Examples](book/examples/)** - See all directive examples

### Releasing

Tag a version (`v0.1.0`) and the GitHub Action will build and publish.

## License

MIT
