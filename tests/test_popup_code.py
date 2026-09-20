"""Build the actual directive and check safe code transport and asset installation."""
import io
import json

import pytest
from bs4 import BeautifulSoup
from sphinx.application import Sphinx


@pytest.mark.parametrize("extension", ["munchboka_edutools.directives.popup_code", "munchboka_edutools"])
def test_popup_code_build(tmp_path, extension):
    source = tmp_path / "src"
    source.mkdir()
    (source / "conf.py").write_text(
        f"extensions=[{extension!r}]\n"
        "master_doc='index'\nproject='Popup code'\n"
    )
    code = 'print(r"\\n </script> </textarea> &amp; ${x} ` ø")'
    (source / "index.rst").write_text(
        'Popup code\n==========\n\n'
        '.. popup-code:: 720 580 "Open code" "My Python window"\n'
        '   :name: exercise\n   :layout: sidebar\n   :predict:\n'
        '   :button-text: Open <code> & run\n\n'
        f'   {code}\n\n.. popup-code::\n'
    )
    output = tmp_path / "html"
    warning = io.StringIO()
    app = Sphinx(str(source), str(source), str(output), str(tmp_path / "doctrees"),
                 "html", status=io.StringIO(), warning=warning, freshenv=True)
    app.build(force_all=True)
    assert not app.statuscode, warning.getvalue()
    assert "ERROR" not in warning.getvalue()
    soup = BeautifulSoup((output / "index.html").read_text(), "html.parser")
    buttons = soup.select("[data-popup-code]")
    assert len(buttons) == 2
    config = json.loads(buttons[0]["data-popup-code"])
    assert config == dict(width=720, height=580, title="My Python window", predict=True, code=code)
    assert buttons[0].text == "Open <code> & run"
    assert "sidebar-cas" in buttons[0].parent["class"]
    assert buttons[0]["aria-controls"] != buttons[1]["aria-controls"]
    assert json.loads(buttons[1]["data-popup-code"])["code"] == ""
    for button in buttons:
        assert soup.find(id=button["aria-controls"])
    for asset in ("js/popup_code.js", "css/popup_code.css", "js/interactiveCode/codeEditor.js"):
        assert (output / "_static/munchboka" / asset).is_file()
    assert soup.select_one('script[src*="/js/popup_code.js"]')
    assert soup.select_one('script[src$="jquery-ui.min.js"]')
    assert soup.select_one('script[src$="codemirror.min.js"]')
