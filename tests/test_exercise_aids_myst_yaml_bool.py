import pytest


def test_exercise_aids_myst_yaml_bool(tmp_path):
    myst = pytest.importorskip("myst_parser")
    _ = myst  # silence unused

    from sphinx.application import Sphinx

    src = tmp_path / "src"
    build = tmp_path / "build"
    doctree = tmp_path / "doctree"
    src.mkdir()
    build.mkdir()
    doctree.mkdir()

    (src / "conf.py").write_text(
        """
project = 'test'
extensions = [
    'myst_parser',
    'munchboka_edutools',
]

myst_enable_extensions = ['colon_fence']
html_theme = 'basic'
master_doc = 'index'
""".lstrip(),
        encoding="utf8",
    )

    # Important: use an actual YAML boolean here (unquoted `true`).
    (src / "index.md").write_text(
        """
# Exercise test

:::{exercise} With aids
---
aids: true
---
Body.
:::

:::{exercise} Without aids
Body.
:::
""".lstrip(),
        encoding="utf8",
    )

    app = Sphinx(
        srcdir=str(src),
        confdir=str(src),
        outdir=str(build),
        doctreedir=str(doctree),
        buildername="html",
        warningiserror=False,
        freshenv=True,
    )
    app.build()

    html = (build / "index.html").read_text(encoding="utf8")
    assert "exercise-aids" in html
