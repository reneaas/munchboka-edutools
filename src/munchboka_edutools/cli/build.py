"""Command-line interface for building enhanced books."""

import click
import subprocess
import sys
import yaml
import tempfile
from pathlib import Path
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup

from ..config.profiles import ProfileManager, BuildProfile
from ..processors import Processor, TypographyProcessor, PageBreakProcessor, MathRenderingProcessor


# Processor registry
PROCESSOR_CLASSES = {
    "typography": TypographyProcessor,
    "page_breaks": PageBreakProcessor,
    "math_rendering": MathRenderingProcessor,
}


class BookBuilder:
    """Orchestrates the book building process."""

    def __init__(self, book_path: Path, profile: BuildProfile, output_dir: Optional[Path] = None):
        """Initialize builder.

        Args:
            book_path: Path to book directory
            profile: Build profile to use
            output_dir: Optional custom output directory
        """
        self.book_path = book_path.resolve()
        self.profile = profile
        self.output_dir = output_dir or self.book_path / "_build" / "html"
        self.processors: List[Processor] = []

        self._initialize_processors()

    def _initialize_processors(self) -> None:
        """Initialize processors from profile configuration."""
        for proc_config in self.profile.processors:
            if not proc_config.enabled:
                continue

            if proc_config.name not in PROCESSOR_CLASSES:
                click.echo(
                    f"⚠️  Warning: Unknown processor '{proc_config.name}', skipping", err=True
                )
                continue

            processor_class = PROCESSOR_CLASSES[proc_config.name]
            processor = processor_class(config=proc_config.settings)
            self.processors.append(processor)

        # Sort by priority
        self.processors.sort(key=lambda p: p.priority)

    def _create_pdf_config(self) -> Path:
        """Create a temporary config file with PDF-specific settings.

        Returns:
            Path to the temporary config file
        """
        # Load the original config
        original_config_path = self.book_path / "_config.yml"
        if not original_config_path.exists():
            raise FileNotFoundError(f"Config file not found: {original_config_path}")

        with open(original_config_path, "r") as f:
            config = yaml.safe_load(f)

        # Ensure sphinx config exists
        if "sphinx" not in config:
            config["sphinx"] = {}
        if "config" not in config["sphinx"]:
            config["sphinx"]["config"] = {}

        # Add imgmath extension for LaTeX math rendering in PDFs
        # This enables proper math rendering in WeasyPrint/PDF output
        sphinx_config = config["sphinx"]["config"]

        # Use imgmath for rendering math as images in PDF
        sphinx_config["imgmath_image_format"] = "svg"
        sphinx_config["imgmath_font_size"] = 12

        # Disable MathJax for PDF output (since it's JavaScript-based)
        sphinx_config["html_math_renderer"] = "imgmath"

        # Add imgmath to extensions if not already present
        if "extra_extensions" not in config["sphinx"]:
            config["sphinx"]["extra_extensions"] = []
        if "sphinx.ext.imgmath" not in config["sphinx"]["extra_extensions"]:
            config["sphinx"]["extra_extensions"].append("sphinx.ext.imgmath")

        # Create temporary config file
        temp_config = tempfile.NamedTemporaryFile(
            mode="w", suffix="_config.yml", dir=self.book_path, delete=False
        )

        with open(temp_config.name, "w") as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        click.echo(f"   📝 Created temporary PDF config with LaTeX math rendering")

        return Path(temp_config.name)

    def build(self) -> bool:
        """Execute the full build process.

        Returns:
            True if successful, False otherwise
        """
        click.echo(f"📚 Building book: {self.book_path.name}")
        click.echo(f"📋 Profile: {self.profile.name} - {self.profile.description}")

        # Step 1: Run Jupyter Book build
        if not self._run_jupyter_book_build():
            return False

        # Step 2: Apply processors
        if not self._apply_processors():
            return False

        click.echo("✅ Build completed successfully!")

        # Show output location
        builder = self.profile.build_options.get("builder", "html")
        if builder == "pdfhtml":
            pdf_path = self.book_path / "_build" / "pdf" / "book.pdf"
            if pdf_path.exists():
                size_mb = pdf_path.stat().st_size / (1024 * 1024)
                click.echo(f"📄 PDF output: {pdf_path} ({size_mb:.1f} MB)")
        else:
            html_index = self.output_dir / "index.html"
            if html_index.exists():
                click.echo(f"🌐 HTML output: {html_index}")

        return True

    def _run_jupyter_book_build(self) -> bool:
        """Run the Jupyter Book build command."""
        builder = self.profile.build_options.get("builder", "html")

        click.echo(f"\n🔨 Running Jupyter Book build (builder: {builder})...")

        # For PDF builds, create a temporary config with LaTeX math rendering
        config_file = None
        if builder == "pdfhtml":
            config_file = self._create_pdf_config()

        cmd = [
            "jb",
            "build",
            str(self.book_path),
            "--builder",
            builder,
        ]

        if config_file:
            cmd.extend(["--config", str(config_file)])

        try:
            result = subprocess.run(
                cmd, check=True, capture_output=True, text=True, cwd=self.book_path.parent
            )

            # Show last few lines of output
            output_lines = result.stdout.split("\n")
            for line in output_lines[-5:]:
                if line.strip():
                    click.echo(f"  {line}")

            return True

        except subprocess.CalledProcessError as e:
            click.echo(f"❌ Jupyter Book build failed:", err=True)
            click.echo(e.stderr, err=True)
            return False
        except FileNotFoundError:
            click.echo(f"❌ 'jb' command not found. Please install jupyter-book:", err=True)
            click.echo("   pip install jupyter-book", err=True)
            return False
        finally:
            # Clean up temporary config file
            if config_file and config_file.exists():
                config_file.unlink()

    def _apply_processors(self) -> bool:
        """Apply all enabled processors to the HTML output."""
        if not self.processors:
            click.echo("\nℹ️  No processors enabled, skipping post-processing")
            return True

        click.echo(f"\n🔧 Applying {len(self.processors)} processor(s)...")

        # Find all HTML files in output
        html_files = list(self.output_dir.rglob("*.html"))

        if not html_files:
            click.echo(f"⚠️  No HTML files found in {self.output_dir}", err=True)
            return False

        click.echo(f"   Found {len(html_files)} HTML file(s)")

        # Shared context for processors
        context = {
            "book_path": self.book_path,
            "output_dir": self.output_dir,
            "profile": self.profile.name,
        }

        # Apply each processor
        for processor in self.processors:
            click.echo(f"   → {processor.name} (priority: {processor.priority})")

            for html_file in html_files:
                try:
                    processor.process_file(html_file, context)
                except Exception as e:
                    click.echo(
                        f"❌ Error processing {html_file.name} with {processor.name}: {e}", err=True
                    )
                    return False

        return True


@click.group()
@click.version_option()
def cli():
    """Muncho - Enhanced book builder for Munchboka educational books.

    Build beautiful, print-ready books from Jupyter Book sources with
    opinionated formatting rules and typography enhancements.
    """
    pass


@cli.command()
@click.argument(
    "book_path", type=click.Path(exists=True, file_okay=False, path_type=Path), required=False
)
@click.option(
    "--profile",
    "-p",
    default="default",
    help="Build profile to use (default, print, web, or custom)",
)
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Custom output directory")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Custom profiles configuration file",
)
@click.option("--list-profiles", is_flag=True, help="List available profiles and exit")
def build(
    book_path: Optional[Path],
    profile: str,
    output: Optional[Path],
    config: Optional[Path],
    list_profiles: bool,
):
    """Build a book with enhanced formatting.

    Examples:

        \b
        # Build with default profile
        muncho build matematikk_1t

        \b
        # Build with print profile for high-quality PDF
        muncho build matematikk_1t --profile print

        \b
        # Use custom configuration
        muncho build matematikk_r1 --config my_profiles.yml --profile custom
    """
    # Load profiles
    profile_manager = ProfileManager(config_file=config)

    if list_profiles:
        click.echo("Available profiles:")
        for profile_name in profile_manager.list_profiles():
            profile_obj = profile_manager.get_profile(profile_name)
            click.echo(f"  • {profile_name}: {profile_obj.description}")
        return

    # Book path is required for actual builds
    if not book_path:
        click.echo("Error: BOOK_PATH is required when not using --list-profiles", err=True)
        sys.exit(1)

    # Get the profile
    try:
        build_profile = profile_manager.get_profile(profile)
    except KeyError as e:
        click.echo(str(e), err=True)
        sys.exit(1)

    # Build the book
    builder = BookBuilder(book_path, build_profile, output_dir=output)
    success = builder.build()

    if not success:
        sys.exit(1)


@cli.command()
def profiles():
    """List all available build profiles."""
    profile_manager = ProfileManager()

    click.echo("📋 Available build profiles:\n")

    for profile_name in profile_manager.list_profiles():
        profile = profile_manager.get_profile(profile_name)
        click.echo(f"  {click.style(profile_name, bold=True)}")
        click.echo(f"    {profile.description}")
        click.echo(f"    Processors: {', '.join(p.name for p in profile.processors if p.enabled)}")
        click.echo()


if __name__ == "__main__":
    cli()
