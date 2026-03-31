"""Tests for the implicit-curve primitive in the plot directive."""

import tempfile
import os
import re
from pathlib import Path
from sphinx.application import Sphinx


def _build(content_lines):
    """Build a Sphinx project with a plot directive and return the first SVG."""
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "source"
        build = Path(tmpdir) / "build"
        doctree = Path(tmpdir) / "doctrees"
        src.mkdir()
        build.mkdir()
        doctree.mkdir()

        (src / "conf.py").write_text(
            "extensions = ['munchboka_edutools']\nexclude_patterns = ['_build']\n"
        )
        content = "Test\n====\n\n.. plot::\n   :width: 70%\n\n"
        for line in content_lines:
            content += f"   {line}\n"
        content += "\n   Caption.\n"
        (src / "index.rst").write_text(content)

        app = Sphinx(
            str(src),
            str(src),
            str(build),
            str(doctree),
            "html",
            warningiserror=False,
            freshenv=True,
        )
        app.build()

        for root, dirs, files in os.walk(str(build)):
            for f in sorted(files):
                if f.endswith(".svg"):
                    return open(os.path.join(root, f)).read()
    return None


def test_implicit_curve_basic():
    """implicit-curve: x**2 + y**2 = 1  should produce a contour path."""
    svg = _build(
        [
            "implicit-curve: x**2 + y**2 = 1",
            "xmin: -2",
            "xmax: 2",
            "ymin: -2",
            "ymax: 2",
        ]
    )
    assert svg is not None
    # Contour produces <path> elements; there should be at least one from the circle
    paths = re.findall(r"<path", svg)
    assert len(paths) >= 1, f"Expected at least 1 <path>, got {len(paths)}"


def test_implicit_curve_with_color():
    """Specifying color should work."""
    svg = _build(
        [
            "implicit-curve: x**2 + y**2 = 4, red",
            "xmin: -3",
            "xmax: 3",
            "ymin: -3",
            "ymax: 3",
        ]
    )
    assert svg is not None
    paths = re.findall(r"<path", svg)
    assert len(paths) >= 1


def test_implicit_curve_with_domain():
    """Specifying (xmin, xmax) domain should work."""
    svg = _build(
        [
            "implicit-curve: x**2 + y**2 = 1, (-1.5, 1.5)",
            "xmin: -3",
            "xmax: 3",
            "ymin: -3",
            "ymax: 3",
        ]
    )
    assert svg is not None
    paths = re.findall(r"<path", svg)
    assert len(paths) >= 1


def test_implicit_curve_with_style_and_color():
    """Specifying both linestyle and color (any order) should work."""
    svg1 = _build(
        [
            "implicit-curve: x**2 + y**2 = 1, dashed, red",
            "xmin: -2",
            "xmax: 2",
            "ymin: -2",
            "ymax: 2",
        ]
    )
    svg2 = _build(
        [
            "implicit-curve: x**2 + y**2 = 1, red, dashed",
            "xmin: -2",
            "xmax: 2",
            "ymin: -2",
            "ymax: 2",
        ]
    )
    assert svg1 is not None
    assert svg2 is not None


def test_implicit_curve_linear_equation():
    """A linear implicit equation like x - 2*y = 1 should work."""
    svg = _build(
        [
            "implicit-curve: x - 2 * y = 1, blue",
            "xmin: -5",
            "xmax: 5",
            "ymin: -5",
            "ymax: 5",
        ]
    )
    assert svg is not None
    paths = re.findall(r"<path", svg)
    assert len(paths) >= 1


def test_implicit_curve_user_example():
    """User's exact example: x**2 - 2 * x + 2 = -2."""
    svg = _build(
        [
            "implicit-curve: x**2 - 2 * x + 2 = -2",
        ]
    )
    assert svg is not None
    # This equation has no real solutions (x^2 - 2x + 4 = 0, discriminant < 0),
    # so there should be no contour path, but the build should not fail.


def test_implicit_curve_with_let():
    """Implicit curve should see let/def macro variables."""
    svg = _build(
        [
            "let: a = 2",
            "implicit-curve: x**2 + y**2 = a**2",
            "xmin: -3",
            "xmax: 3",
            "ymin: -3",
            "ymax: 3",
        ]
    )
    assert svg is not None
    paths = re.findall(r"<path", svg)
    assert len(paths) >= 1


def test_implicit_curve_all_options():
    """Full syntax: equation, (xmin, xmax), linestyle, color."""
    svg = _build(
        [
            "implicit-curve: x**2 + y**2 = 4, (-2.5, 2.5), dotted, green",
            "xmin: -3",
            "xmax: 3",
            "ymin: -3",
            "ymax: 3",
        ]
    )
    assert svg is not None
    paths = re.findall(r"<path", svg)
    assert len(paths) >= 1
