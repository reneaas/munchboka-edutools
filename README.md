# munchboka-edutools

Reusable Sphinx / Jupyter Book directives and assets for Norwegian educational content.

## Install

```bash
pip install munchboka-edutools
```

## Usage (Jupyter Book `_config.yml`)

```yaml
sphinx:
  extra_extensions:
    - munchboka_edutools
```

All packaged directives are auto-registered. Static assets are placed under `_static/munchboka/` during the build.

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

### Releasing

Tag a version (`v0.1.0`) and the GitHub Action will build and publish.

## License

MIT
