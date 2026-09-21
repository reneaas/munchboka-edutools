"""Build the same notebook application outside Sphinx."""

from pathlib import Path

import click

from ..notebook.site import build_site


@click.group()
def notebook():
    """Lag en norsk notebook-nettside med Python i nettleseren."""


@notebook.command("build")
@click.option(
    "--contents",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Mappe med .ipynb-filer og tilhørende data. Standard: tre eksempeloppgaver.",
)
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), default="_build/notebook", show_default=True
)
@click.option("--title", default="Munchboka · Notebook", show_default=True)
def build(contents, output, title):
    """Bygg statiske filer som kan publiseres på en vanlig webserver."""
    try:
        destination = build_site(output, contents, title)
    except (ValueError, RuntimeError, OSError) as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"Notebook-nettsiden er klar: {destination}")
    click.echo(f'Forhåndsvisning: python -m http.server 8000 --directory "{destination}"')
