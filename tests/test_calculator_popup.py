"""Build the standalone extension, including nested HTML/dirhtml URLs."""
import io
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from sphinx.application import Sphinx


@pytest.mark.parametrize("builder", ["html", "dirhtml", "text"])
def test_calculator_popup_build(tmp_path, builder):
    src = tmp_path / "src"
    src.mkdir()
    (src / "chapter").mkdir()
    (src / "conf.py").write_text(
        "extensions=['munchboka_edutools.directives.calculator_popup']\n"
        "master_doc='index'\nproject='Calculator test'\n", encoding="utf8"
    )
    (src / "index.rst").write_text("Calculator\n==========\n\n.. toctree::\n\n   chapter/practice\n")
    (src / "chapter/practice.rst").write_text(
        'Practice\n========\n\n.. calculator-popup::\n'
        '   :name: algebra\n   :button-text: Open <calculator> & practice\n'
        '   :title: Test "calculator"\n   :layout: sidebar\n\n'
        '.. calculator-popup:: 420 820\n', encoding="utf8"
    )
    out = tmp_path / "out"
    warnings = io.StringIO()
    app = Sphinx(str(src), str(src), str(out), str(tmp_path / "doctrees"), builder, status=io.StringIO(), warning=warnings, freshenv=True)
    app.build(force_all=True)
    assert not app.statuscode, warnings.getvalue()
    assert "ERROR" not in warnings.getvalue()
    if builder == "text":
        assert "CW-style scientific calculator" in (out / "chapter/practice.txt").read_text()
        return
    html = out / ("chapter/practice.html" if builder == "html" else "chapter/practice/index.html")
    soup = BeautifulSoup(html.read_text(), "html.parser")
    buttons = soup.select(".cw-popup-button")
    assert len(buttons) == 2
    assert buttons[0].text == "Open <calculator> & practice"
    assert buttons[0]["data-cw-title"] == 'Test "calculator"'
    assert buttons[0]["data-cw-id"] != buttons[1]["data-cw-id"]
    assert buttons[1]["data-cw-width"] == "420"
    for button in buttons:
        assert (html.parent / button["data-cw-src"]).resolve().is_file()
    assert (out / "_static/munchboka/calculator/vendor/decimal.mjs").is_file()
    assert (out / "_static/munchboka/js/calculator_popup.js").is_file()
    first_ids = [b["data-cw-id"] for b in buttons]
    app.build(force_all=True)
    rebuilt = BeautifulSoup(html.read_text(), "html.parser")
    assert [b["data-cw-id"] for b in rebuilt.select(".cw-popup-button")] == first_ids


def test_invalid_dimensions_report_build_warning(tmp_path):
    (tmp_path / "conf.py").write_text("extensions=['munchboka_edutools.directives.calculator_popup']\nmaster_doc='index'\n")
    (tmp_path / "index.rst").write_text("Test\n====\n\n.. calculator-popup:: 100 200\n")
    warnings = io.StringIO()
    app = Sphinx(str(tmp_path), str(tmp_path), str(tmp_path / "out"), str(tmp_path / "cache"), "html", status=io.StringIO(), warning=warnings)
    app.build(force_all=True)
    assert "width must be at least 280" in warnings.getvalue()
