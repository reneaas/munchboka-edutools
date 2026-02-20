from pathlib import Path

from sphinx.application import Sphinx


def _make_source(src: Path) -> None:
    (src / "conf.py").write_text(
        """
project = 'test'
extensions = [
    'munchboka_edutools',
]

html_theme = 'basic'
""".lstrip(),
        encoding="utf8",
    )

    (src / "index.rst").write_text(
        """
Exercise test
=============

.. exercise:: With aids
   :aids: true

   This exercise allows digital aids.

.. exercise:: Without aids

   This exercise does not.
""".lstrip(),
        encoding="utf8",
    )


def test_exercise_aids_icon(tmp_path):
    src = tmp_path / "src"
    build = tmp_path / "build"
    doctree = tmp_path / "doctree"
    src.mkdir()
    build.mkdir()
    doctree.mkdir()
    _make_source(src)

    app = Sphinx(
        srcdir=str(src),
        confdir=str(src),
        outdir=str(build),
        doctreedir=str(doctree),
        buildername="html",
        warningiserror=True,
        freshenv=True,
    )
    app.build()

    html = (build / "index.html").read_text(encoding="utf8")
    assert "exercise-aids" in html

    css = (build / "_static" / "munchboka" / "css" / "admonitions.css").read_text(encoding="utf8")
    assert "light_mode/computer.svg" in css
    assert "dark_mode/computer.svg" in css

    # Ensure the referenced icon actually gets packaged into the build output
    assert (
        build / "_static" / "munchboka" / "icons" / "solid" / "light_mode" / "computer.svg"
    ).exists()
    assert (
        build / "_static" / "munchboka" / "icons" / "solid" / "dark_mode" / "computer.svg"
    ).exists()
