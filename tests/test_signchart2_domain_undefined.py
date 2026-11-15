from io import StringIO

import matplotlib
import pytest
import sympy as sp
from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace

matplotlib.use("Agg")

from munchboka_edutools.directives import signchart2
from munchboka_edutools.directives.signchart2 import _parse_domain_option, plot


def test_signchart2_log_domain_shows_undefined_region_as_times():
    # log(x, 2) is undefined for x <= 0 over the reals.
    fig, ax = plot("log(x, 2)", include_factors=False)

    times_count = sum(1 for t in ax.texts if t.get_text() == "$\\times$")

    # Expect one \times on the x=0 boundary point and one \times in the (-∞, 0) interval.
    assert times_count == 2

    matplotlib.pyplot.close(fig)


@pytest.mark.parametrize(
    "expression, domain, zeros, crosses",
    [
        ("x**2 - 4", (1, 3), 1, 0),
        ("(x**2 - 1)/(x**2 - 4)", (-1.5, 1.5), 2, 0),
        ("log(x)", (2, 3), 0, 0),
        ("sin(x)", (-1, 1), 1, 0),
    ],
)
def test_explicit_domain_excludes_outside_breakpoints(expression, domain, zeros, crosses):
    fig, ax = plot(expression, domain=domain, include_factors=False)
    try:
        texts = [text.get_text() for text in ax.texts]
        assert texts.count("$0$") == zeros
        assert texts.count("$\\times$") == crosses
    finally:
        matplotlib.pyplot.close(fig)


@pytest.mark.parametrize(
    "expression, domain",
    [("x - 2", (1, 1.1)), ("x", (0, 0.1)), ("x - 1", (0.9, 1))],
)
def test_domain_bounds_all_sign_samples_including_factor_rows(monkeypatch, expression, domain):
    samples = []
    original = signchart2._eval_sign_at

    def record_sample(expr, x, x0, *args, **kwargs):
        samples.append(x0)
        return original(expr, x, x0, *args, **kwargs)

    monkeypatch.setattr(signchart2, "_eval_sign_at", record_sample)
    fig, ax = plot(expression, domain=domain, include_factors=True)
    try:
        assert samples
        assert all(domain[0] <= sample <= domain[1] for sample in samples)
        # Two horizontal sign lines: one factor and the function.
        horizontal = [
            line for line in ax.lines
            if len(set(line.get_ydata())) == 1 and line.get_ydata()[0] < 0
        ]
        assert len(horizontal) == 2
        expected_style = "-" if expression == "x" else "--"
        assert all(line.get_linestyle() == expected_style for line in horizontal)
    finally:
        matplotlib.pyplot.close(fig)


def test_periodic_product_keeps_all_zeros_in_requested_domain():
    fig, ax = plot(
        "sin(pi*x/6)*(1 + 2*cos(pi*x/6))",
        domain=(-5, 5),
        include_factors=True,
    )
    try:
        function_y = min(text.get_position()[1] for text in ax.texts)
        zeros = [
            text for text in ax.texts
            if text.get_text() == "$0$" and text.get_position()[1] == function_y
        ]
        assert len(zeros) == 3  # -4, 0, 4
        assert sum(text.get_text() == "$0$" for text in ax.texts) == 6
    finally:
        matplotlib.pyplot.close(fig)


def test_domain_parser_accepts_numeric_expressions_and_preserves_assumptions():
    domain, assumptions = _parse_domain_option("(-2*pi, 2*pi)")
    assert domain == pytest.approx((-2 * float(sp.pi), 2 * float(sp.pi)))
    assert assumptions is None
    assert _parse_domain_option("a > 0") == (None, "a > 0")


@pytest.mark.parametrize("domain", ["(3, 1)", "(1, 1)", "(-oo, 2)", "(a, 2)", "(1,)"])
def test_invalid_interval_is_reported(domain):
    with pytest.raises(ValueError, match="domain"):
        _parse_domain_option(domain)


@pytest.mark.parametrize(
    "body, valid",
    [
        ("function: x**2 - 4\nfactors: false\ndomain: (1, 3)", True),
        ("---\nfunction: x**2 - 4\nfactors: false\ndomain: (1, pi)\n---", True),
        ("function: x**2 - 4\ndomain: (3, 1)", False),
    ],
)
def test_domain_primitive_in_sphinx_build(tmp_path, body, valid):
    src = tmp_path / "src"
    src.mkdir()
    (src / "conf.py").write_text(
        "extensions = ['myst_parser', 'munchboka_edutools.directives.signchart2']\n"
        "html_theme = 'basic'\nmaster_doc = 'index'\nproject = 'Signchart domain'\n"
    )
    (src / "index.md").write_text(f"# Domain\n\n```{{signchart-2}}\n{body}\n```\n")
    warnings = StringIO()
    with docutils_namespace():
        app = Sphinx(
            str(src),
            str(src),
            str(tmp_path / "out"),
            str(tmp_path / "tree"),
            "html",
            status=StringIO(),
            warning=warnings,
            freshenv=True,
        )
        app.build()
    if valid:
        assert not warnings.getvalue()
        svg_files = list((src / "_static" / "signchart").glob("*.svg"))
        assert len(svg_files) == 1
        svg = svg_files[0].read_text()
        assert svg.count("<!-- $0$ -->") == 1
        assert "<!-- $-2$ -->" not in svg
        assert "graph-inline-svg" in (tmp_path / "out" / "index.html").read_text()
    else:
        assert "domain must be a finite interval" in warnings.getvalue()
        assert not list(src.glob("_static/signchart/*.svg"))
