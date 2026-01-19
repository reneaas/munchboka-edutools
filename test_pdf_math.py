#!/usr/bin/env python3
"""Test script to verify PDF math rendering configuration."""

import sys
import yaml
import tempfile
from pathlib import Path

# Add src to path for local testing
sys.path.insert(0, str(Path(__file__).parent / "src"))

from munchboka_edutools.config.profiles import ProfileManager
from munchboka_edutools.cli.build import BookBuilder


def test_pdf_config_generation():
    """Test that PDF config is generated correctly."""
    print("🧪 Testing PDF config generation...")

    # Get the print profile
    profile_manager = ProfileManager()
    print_profile = profile_manager.get_profile("print")

    print(f"✓ Loaded print profile: {print_profile.description}")
    print(f"✓ Builder: {print_profile.build_options.get('builder')}")

    # Find a book to test with
    test_books = [
        Path(__file__).parent.parent / "matematikk_1t",
        Path(__file__).parent.parent / "matematikk_r1",
    ]

    book_path = None
    for path in test_books:
        if path.exists() and (path / "_config.yml").exists():
            book_path = path
            break

    if not book_path:
        print("⚠️  No test book found, skipping actual config generation test")
        return True

    print(f"✓ Using test book: {book_path.name}")

    # Create a BookBuilder instance
    try:
        builder = BookBuilder(book_path, print_profile)
        print("✓ BookBuilder initialized successfully")

        # Test config generation
        temp_config = builder._create_pdf_config()
        print(f"✓ Temporary config created: {temp_config}")

        # Verify the config content
        with open(temp_config, "r") as f:
            config = yaml.safe_load(f)

        # Check that sphinx.ext.imgmath is added
        assert "sphinx" in config, "Missing 'sphinx' key"
        assert "extra_extensions" in config["sphinx"], "Missing 'extra_extensions'"
        assert (
            "sphinx.ext.imgmath" in config["sphinx"]["extra_extensions"]
        ), "Missing sphinx.ext.imgmath extension"

        # Check imgmath config
        assert "config" in config["sphinx"], "Missing 'config' in sphinx"
        sphinx_config = config["sphinx"]["config"]
        assert (
            sphinx_config.get("imgmath_image_format") == "svg"
        ), "imgmath_image_format not set to svg"
        assert (
            sphinx_config.get("html_math_renderer") == "imgmath"
        ), "html_math_renderer not set to imgmath"

        print("✓ Config contains correct imgmath settings")

        # Verify original macros are preserved
        if "mathjax3_config" in sphinx_config:
            print("✓ Original mathjax3_config preserved")

        # Clean up
        temp_config.unlink()
        print("✓ Temporary config cleaned up")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_profile_configuration():
    """Test that profiles are configured correctly."""
    print("\n🧪 Testing profile configuration...")

    profile_manager = ProfileManager()

    # Test print profile
    print_profile = profile_manager.get_profile("print")
    assert (
        print_profile.build_options.get("builder") == "pdfhtml"
    ), "Print profile should use pdfhtml builder"
    print("✓ Print profile uses pdfhtml builder")

    # Test that math_rendering processor is enabled
    math_proc = next((p for p in print_profile.processors if p.name == "math_rendering"), None)
    assert math_proc is not None, "math_rendering processor not found"
    assert math_proc.enabled, "math_rendering processor should be enabled"
    print("✓ Math rendering processor is enabled in print profile")

    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Testing PDF Math Rendering Implementation")
    print("=" * 60)

    success = True

    # Run tests
    success &= test_profile_configuration()
    success &= test_pdf_config_generation()

    print("\n" + "=" * 60)
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
