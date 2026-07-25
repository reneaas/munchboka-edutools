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
Hint toggle
===========

.. hints:: Hint 1

   Bruk definisjonen.
""".lstrip(),
        encoding="utf8",
    )


def test_hint_toggle_build_uses_hardened_transition_script(tmp_path):
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
    assert 'class="hint-toggle"' in html
    assert "hint-content" in html

    hint_js = (build / "_static" / "munchboka" / "js" / "hint.js").read_text(encoding="utf8")
    assert 'buttonClass: "hint-toggle"' in hint_js
    assert "cancelContentTransition" in hint_js
    assert "_munchbokaToggleCleanup" in hint_js
    assert "munchbokaToggleBound" in hint_js
